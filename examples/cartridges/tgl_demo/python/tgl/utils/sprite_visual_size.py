"""Utility to derive on-screen visual footprint of sprites for hitbox binding.

The goal is to make ColliderComponent sizes *derived from* the visible sprite
rather than arbitrary magic numbers. This replicates (and exposes) the
normalization + base_scale math that RenderSystem applies.

For .egg assets (current TGL demo):
  - egg-texture-cards produces geometry whose tight bounds reflect the source
    frame pixel size (e.g. ship frames are ~92x120 logical units in the .egg).
  - RenderSystem does: model.setScale(1.0 / max(extent_x, extent_z))
  - Then every frame: final_scale = 0.5 * transform.scale  (base_scale = 0.5)
  - Result: a sprite with Transform(scale=1.0) occupies a predictable rectangle
    in aspect2d units.

This helper lets cartridge code ask "how big will this look at scale=1?" at
spawn time (cheap model load, no scene graph required) and then choose a
reasonable hitbox fraction (e.g. 65-80% of visual for "bound to sprite" while
still allowing some traditional NES-style forgiveness/graze area).
"""
from __future__ import annotations

from typing import Optional, Tuple

# Panda3D loader protocol (ShowBase.loader or direct Loader)
try:
    from panda3d.core import Loader as PandaLoader  # type: ignore
except Exception:  # pragma: no cover
    PandaLoader = object  # type: ignore


# The same constant used in RenderSystem._update_node_transform
RENDER_BASE_SCALE = 0.5


def get_visual_size(image_path: str, loader: Optional[object] = None) -> Tuple[float, float]:
    """Return the effective (width, height) in aspect2d units that a sprite
    using this asset will occupy when TransformComponent(scale_x=1, scale_y=1).

    For .egg files this performs the same tight-bounds normalization that
    RenderSystem does, then multiplies by the render base scale (0.5).

    The returned size is the *full* footprint (not half-extents).

    Args:
        image_path: Path as used by SpriteComponent (e.g. "assets/sprites/ship/ship.egg").
                    Must be resolvable by the provided (or global) Panda loader.
        loader: A Panda3D loader object (base.loader). If None, the function
                will attempt to use the global `base.loader` if available in
                the current ShowBase (best-effort; prefer passing it explicitly).

    Returns:
        (visual_width, visual_height) for scale=1.0
    """
    if not image_path:
        # Fallback for colored cards etc.: treat as a unit square before base scale
        return (RENDER_BASE_SCALE * 1.0, RENDER_BASE_SCALE * 1.0)

    lower = image_path.lower()
    if lower.endswith(".egg"):
        return _get_egg_visual_size(image_path, loader)

    # PNG / texture path (CardMaker path in RenderSystem creates a square -0.5..0.5 card)
    # Current render path does *not* auto-correct for texture aspect on the CardMaker;
    # the quad is square and texture stretches. The effective displayed size at
    # scale=1 is therefore a square of side RENDER_BASE_SCALE.
    # Future improvement: load the texture, compute aspect, and return a
    # non-square rect that matches what a corrected card would produce.
    return (RENDER_BASE_SCALE * 1.0, RENDER_BASE_SCALE * 1.0)


def _get_egg_visual_size(egg_path: str, loader: Optional[object]) -> Tuple[float, float]:
    """Internal: load .egg, replicate RenderSystem normalization, apply base scale."""
    effective_loader = loader
    if effective_loader is None:
        # Best-effort fallback (works inside a running ShowBase)
        try:
            from direct.showbase.ShowBaseGlobal import globalClock  # noqa: F401
            from direct.showbase import ShowBase  # type: ignore
            # ShowBase has a module-level `loader` once initialized
            import builtins
            if hasattr(builtins, "base") and hasattr(builtins.base, "loader"):
                effective_loader = builtins.base.loader
        except Exception:
            effective_loader = None

    if effective_loader is None:
        # Last resort: cannot compute precisely without a loader. Return a
        # conservative default that at least keeps things visible.
        # (Callers should always pass the loader in production cartridge code.)
        print(f"[sprite_visual_size] WARNING: no loader available for {egg_path}; "
              "returning conservative default visual size.")
        return (0.4, 0.5)

    try:
        model = effective_loader.loadModel(egg_path)
    except Exception as e:
        print(f"[sprite_visual_size] ERROR loading egg {egg_path}: {e}")
        return (0.4, 0.5)

    if model is None or model.isEmpty():
        print(f"[sprite_visual_size] ERROR: empty model for {egg_path}")
        return (0.4, 0.5)

    bounds = model.getTightBounds()
    if not bounds:
        # No geometry bounds — fall back
        model.removeNode()
        return (RENDER_BASE_SCALE * 1.0, RENDER_BASE_SCALE * 1.0)

    min_pt, max_pt = bounds
    extent_x = max_pt.x - min_pt.x
    extent_z = max_pt.z - min_pt.z
    max_extent = max(extent_x, extent_z)

    if max_extent <= 0:
        model.removeNode()
        return (RENDER_BASE_SCALE * 1.0, RENDER_BASE_SCALE * 1.0)

    # This is exactly what RenderSystem does to normalize the model to ~1 unit max
    norm_scale = 1.0 / max_extent

    # After normalization the model spans:
    #   w = extent_x * norm_scale
    #   h = extent_z * norm_scale
    # Then RenderSystem multiplies the whole node by base_scale * user_scale
    visual_w = extent_x * norm_scale * RENDER_BASE_SCALE
    visual_h = extent_z * norm_scale * RENDER_BASE_SCALE

    # Cleanup the temporary node (it is not parented anywhere)
    model.removeNode()

    return (visual_w, visual_h)


def compute_hitbox_size(visual_size: Tuple[float, float],
                        factor: float = 0.70,
                        min_size: float = 0.05) -> Tuple[float, float]:
    """Given a (w, h) visual size at scale=1, return a suggested collider full size.

    The factor lets you choose how tightly the hitbox should hug the visible art.
    Typical retro values are 0.6–0.85 (smaller = more forgiving "graze" area).

    Returns (width, height) suitable for ColliderComponent.size (full extents).
    """
    w, h = visual_size
    hw = max(min_size, w * factor)
    hh = max(min_size, h * factor)
    return (hw, hh)
