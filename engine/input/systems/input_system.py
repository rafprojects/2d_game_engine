from typing import List, Dict

from direct.showbase.ShowBase import ShowBase
from panda3d.core import InputDevice, ButtonHandle

from engine.core.system import System
from engine.input.components.input_component import InputComponent
from engine.input.input_bindings import InputBinding

# Panda3D Gamepad Axis Mapping
PANDA_GAMEPAD_AXES = {
    "lstick_x": InputDevice.Axis.left_x,
    "lstick_y": InputDevice.Axis.left_y,
    "rstick_x": InputDevice.Axis.right_x,
    "rstick_y": InputDevice.Axis.right_y,
    "ltrigger": InputDevice.Axis.left_trigger,
    "rtrigger": InputDevice.Axis.right_trigger,
}

class InputSystem(System):
    """
    Handles input by polling devices and updating InputComponents based on their bindings.
    This system is designed to be flexible: changes to an entity's InputComponent.action_bindings
    at runtime (e.g., by a UI for control remapping) will be automatically used.
    """
    def __init__(self, world, showbase_instance):
        super().__init__(world)
        self.showbase = showbase_instance
        self._gamepads: List[InputDevice] = []
        self._setup_device_listener()
        self._discover_gamepads()

    def _setup_device_listener(self):
        """Sets up listeners for gamepad connection and disconnection events."""
        self.showbase.accept("connect-device", self._handle_connect_device)
        self.showbase.accept("disconnect-device", self._handle_disconnect_device)

    def _handle_connect_device(self, device: InputDevice):
        """Handles new device connections; if it's a gamepad, rediscover."""
        if device.get_device_class() == InputDevice.DeviceClass.gamepad:
            print(f"InputSystem: Gamepad connected - {device.name}")
            self._discover_gamepads()

    def _handle_disconnect_device(self, device: InputDevice):
        """Handles device disconnections; if it's a gamepad, rediscover."""
        if device.get_device_class() == InputDevice.DeviceClass.gamepad:
            print(f"InputSystem: Gamepad disconnected - {device.name}")
            self._discover_gamepads()

    def _discover_gamepads(self):
        """Discovers all currently connected gamepads."""
        self._gamepads.clear()
        # Ensure base.devices is available
        if hasattr(self.showbase, 'devices') and self.showbase.devices is not None:
            devices = self.showbase.devices.get_devices(InputDevice.DeviceClass.gamepad)
            for device in devices:
                self._gamepads.append(device)
                print(f"InputSystem: Found gamepad - {device.name} (ID: {len(self._gamepads)-1})")
        else:
            print("InputSystem: Warning - ShowBase devices not available for gamepad discovery.")

    def on_entity_added(self, entity_id: str):
        """No specific action needed on entity add for polling system."""
        # InputComponent.__post_init__ handles initialization of its dictionaries.

    def on_component_added(self, entity_id: str, component_instance: object):
        """No specific action needed on component add for polling system."""
        # InputComponent.__post_init__ handles initialization.

    def on_entity_removed(self, entity_id: str, entity_components):
        """No specific cleanup needed as this system polls."""

    def on_component_removed(self, entity_id: str, component_instance: object):
        """No specific cleanup needed if the removed component is InputComponent."""

    def update(self, dt):
        """Main update loop. Polls devices and updates all InputComponents."""
        if self.showbase.devices is not None:
            self.showbase.devices.update()

        entities = self.world.get_entities_with_components(InputComponent)
        for entity in entities:
            input_comp = self.world.get_component(entity.id, InputComponent)
            if input_comp:
                self._update_input_component_states(input_comp)

    def _update_input_component_states(self, input_comp: InputComponent):
        """
        Calculates the new state of all actions in an InputComponent
        based on current device inputs and defined bindings.
        Updates action_active, action_just_pressed, and action_just_released.
        """
        newly_calculated_active_states: Dict[str, bool] = {}

        # Determine current active state for each action based on its bindings
        for action_name, bindings_list in input_comp.action_bindings.items():
            is_triggered = self._check_action_triggered(bindings_list)
            newly_calculated_active_states[action_name] = is_triggered

        # Update just_pressed, just_released, action_active, and _previous_action_active
        for action_name in input_comp.action_bindings.keys():
            current_is_active = newly_calculated_active_states.get(action_name, False)
            previous_was_active = input_comp._previous_action_active.get(action_name, False)

            input_comp.action_just_pressed[action_name] = current_is_active and not previous_was_active
            input_comp.action_just_released[action_name] = not current_is_active and previous_was_active
            
            input_comp.action_active[action_name] = current_is_active
            input_comp._previous_action_active[action_name] = current_is_active

    def _check_action_triggered(self, bindings_list: List[InputBinding]) -> bool:
        """Checks if an action is triggered by any of its bindings."""
        for binding in bindings_list:
            if self._is_binding_active(binding):
                return True
        return False

    def _is_binding_active(self, binding: InputBinding) -> bool:
        """Checks if a single InputBinding is currently active by dispatching to helper methods."""
        if binding.input_type == "key":
            return self._is_key_active(binding)
        elif binding.input_type == "mouse_button":
            return self._is_mouse_button_active(binding)
        elif binding.input_type == "gamepad_button":
            return self._is_gamepad_button_active(binding)
        elif binding.input_type == "gamepad_axis":
            return self._is_gamepad_axis_active(binding)
        return False

    def _is_key_active(self, binding: InputBinding) -> bool:
        """Checks if a key binding is active."""
        return self.showbase.mouseWatcherNode.is_button_down(binding.event_name)

    def _is_mouse_button_active(self, binding: InputBinding) -> bool:
        """Checks if a mouse button binding is active."""
        return self.showbase.mouseWatcherNode.is_button_down(binding.event_name)

    def _is_gamepad_button_active(self, binding: InputBinding) -> bool:
        """Checks if a gamepad button binding is active."""
        for gamepad_idx, gamepad in enumerate(self._gamepads):
            if binding.gamepad_id is None or binding.gamepad_id == gamepad_idx:
                button_handle = gamepad.find_button(binding.event_name)
                if button_handle != ButtonHandle.none() and gamepad.is_button_down(button_handle):
                    return True
        return False

    def _is_gamepad_axis_active(self, binding: InputBinding) -> bool:
        """Checks if a gamepad axis binding is active."""
        target_axis_enum = PANDA_GAMEPAD_AXES.get(binding.event_name)
        if not target_axis_enum:
            return False

        for gamepad_idx, gamepad in enumerate(self._gamepads):
            if self._is_gamepad_match(binding, gamepad_idx):
                if self._check_axis_value(gamepad, target_axis_enum, binding):
                    return True
        return False

    def _is_gamepad_match(self, binding: InputBinding, gamepad_idx: int) -> bool:
        """Checks if the binding applies to the given gamepad index."""
        return binding.gamepad_id is None or binding.gamepad_id == gamepad_idx

    def _check_axis_value(self, gamepad: InputDevice, axis_enum, binding: InputBinding) -> bool:
        """Checks if the gamepad's axis value meets the binding's criteria."""
        axis_state = gamepad.find_axis(axis_enum)
        if not axis_state.known:
            return False

        value = axis_state.value
        threshold = binding.axis_threshold
        direction = binding.axis_direction

        if direction == "positive" and value > threshold:
            return True
        elif direction == "negative" and value < -threshold:
            return True
        elif direction == "any" and abs(value) > threshold:
            return True
        return False
