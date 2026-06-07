"""Built-in save-state provider that serializes the ECS World.

The engine ships this so cartridges get working save/load out of the box without
each having to implement :class:`~engine.save_state.manager.SaveStateProvider`
themselves. It captures every entity (id + name) and the plain-data fields of each
attached component.

Serialization rules
-------------------
* **Dataclass components** (the common case, e.g. ``TransformComponent``): their
  declared fields are captured.
* **Other components**: their instance ``__dict__`` is captured.
* Only msgpack/JSON-safe values are stored: ``None``/``bool``/``int``/``float``/
  ``str`` and nested ``list``/``dict`` of those. Engine/runtime objects (Panda3D
  nodes, textures, ``Vec3`` …) are skipped; the ``panda_node`` attribute is always
  skipped because rendering systems rebuild it on restore.
* A component may take full control by implementing ``to_dict(self)`` and a
  ``from_dict(cls, data)`` classmethod; when present these are used verbatim.

Components are resolved on restore by ``"<module>:<qualname>"``. If a component
class has moved or been renamed, register the replacement with
:meth:`WorldSaveProvider.register_component`.
"""

from __future__ import annotations

import dataclasses
import importlib
import uuid
from typing import Any, Dict, List, Optional, Type

from engine.core.entity import Entity
from engine.core.events import EntityCreatedEvent
from engine.save_state.errors import SaveStateError

_PRIMITIVE_TYPES = (type(None), bool, int, float, str)


def _is_serializable(value: Any) -> bool:
    """Return True for values safe to store in a save file."""
    if isinstance(value, _PRIMITIVE_TYPES):
        return True
    if isinstance(value, (list, tuple)):
        return all(_is_serializable(item) for item in value)
    if isinstance(value, dict):
        return all(
            isinstance(key, str) and _is_serializable(val) for key, val in value.items()
        )
    return False


def _component_key(component_type: type) -> str:
    """Stable identifier used to resolve a component class on restore."""
    return f"{component_type.__module__}:{component_type.__qualname__}"


class WorldSaveProvider:
    """Default :class:`SaveStateProvider` that (de)serializes the ECS World."""

    #: Attributes never captured (runtime handles rebuilt by systems on restore).
    SKIP_ATTRS = frozenset({"panda_node"})

    def __init__(self, clear_on_restore: bool = True) -> None:
        self.clear_on_restore = clear_on_restore
        self._registry: Dict[str, Type[Any]] = {}

    # -- component class resolution -------------------------------------
    def register_component(
        self, component_type: type, key: Optional[str] = None
    ) -> None:
        """Override how a component class is resolved on restore (e.g. after a rename)."""
        self._registry[key or _component_key(component_type)] = component_type

    def _resolve_component(self, key: str) -> type:
        if key in self._registry:
            return self._registry[key]
        module_name, _, qualname = key.partition(":")
        if not module_name.startswith("engine."):
            raise SaveStateError(
                f"Refusing to import module outside engine namespace: {module_name!r}. "
                "Register a replacement via WorldSaveProvider.register_component()."
            )
        obj: Any = importlib.import_module(module_name)
        for part in qualname.split("."):
            obj = getattr(obj, part)
        return obj

    # -- capture --------------------------------------------------------
    def capture(self, world: Any) -> Dict[str, Any]:
        entities: List[Dict[str, Any]] = []
        for entity_id, entity in world.entities.items():
            components: List[Dict[str, Any]] = []
            for component_type, component in world.components.get(
                entity_id, {}
            ).items():
                components.append(
                    {
                        "type": _component_key(component_type),
                        "data": self._capture_component(component),
                    }
                )
            entities.append(
                {"id": str(entity_id), "name": entity.name, "components": components}
            )
        return {"entities": entities}

    def _capture_component(self, component: Any) -> Dict[str, Any]:
        to_dict = getattr(component, "to_dict", None)
        if callable(to_dict):
            return dict(to_dict())
        if dataclasses.is_dataclass(component):
            source = {
                field.name: getattr(component, field.name)
                for field in dataclasses.fields(component)
            }
        else:
            source = dict(vars(component))
        data: Dict[str, Any] = {}
        for name, value in source.items():
            if name in self.SKIP_ATTRS or not _is_serializable(value):
                continue
            data[name] = list(value) if isinstance(value, tuple) else value
        return data

    # -- restore --------------------------------------------------------
    def restore(self, world: Any, payload: Dict[str, Any]) -> None:
        if self.clear_on_restore:
            for entity_id in list(world.entities.keys()):
                world.remove_entity(entity_id)
        for record in payload.get("entities", []):
            entity = Entity(record.get("name"))
            entity.id = uuid.UUID(str(record["id"]))
            if record.get("name"):
                entity.name = record["name"]
            world.entities[entity.id] = entity
            world.components[entity.id] = {}
            world.event_manager.publish(EntityCreatedEvent(entity.id))
            for component_record in record.get("components", []):
                component_type = self._resolve_component(component_record["type"])
                instance = self._build_component(
                    component_type, component_record.get("data", {})
                )
                world.add_component(entity.id, instance)

    def _build_component(self, component_type: type, data: Dict[str, Any]) -> Any:
        from_dict = getattr(component_type, "from_dict", None)
        if callable(from_dict):
            return from_dict(data)
        if dataclasses.is_dataclass(component_type):
            field_names = {field.name for field in dataclasses.fields(component_type)}
            kwargs = {key: val for key, val in data.items() if key in field_names}
            try:
                return component_type(**kwargs)
            except TypeError as exc:
                raise SaveStateError(
                    f"Failed to construct {component_type.__qualname__}: {exc}. "
                    "Save data may be incompatible with the current component definition."
                ) from exc
        instance = object.__new__(component_type)  # type: ignore[misc]
        for key, value in data.items():
            setattr(instance, key, value)
        return instance
