"""
VirtualPlayfield - virtual retro pixel space and its mapping to render coordinates.

Retro cartridges think in *pixels* (a 256x240 NES-like playfield, integer
geometry, velocities in pixels-per-tick, subpixel = 1/256 of a pixel). The
engine's RenderSystem, however, draws in Panda3D aspect2d units: it creates a
1x1 CardMaker card and scales it by ``base_scale (0.5) * Transform.scale``
(see engine/graphics/systems/render_system.py).

This class is the single place where those two worlds meet:

- ``to_render(x_px, y_px)`` converts a pixel-space position (Y-up, origin at
  the bottom-left of the playfield) to an aspect2d position centered on the
  screen.
- ``size_to_render_scale(w_px, h_px)`` converts a pixel-space size to the
  ``Transform.scale_x/scale_y`` values that make the rendered rect exactly
  that many pixels wide/tall on the playfield - i.e. **visual size equals
  collision size by construction** (it divides out the RenderSystem's
  base_scale so cartridges never need to know about it).

The default 256x240 playfield maps its full height onto aspect2d's full
vertical extent (2.0 units, -1..+1), giving ``units_per_px = 2/240``. Width is
then 256 * 2/240 ~= 2.133 units (+-1.067) which fits a 4:3 window's +-1.333
horizontal extent. On extremely tall/narrow windows the left/right playfield
edges may be cropped (cosmetic only).

Pure Python, no Panda3D import - safe for headless tests and cartridges.
"""

from __future__ import annotations


class VirtualPlayfield:
    """Maps a virtual pixel playfield (Y-up, origin bottom-left) to aspect2d.

    Args:
        width_px / height_px: playfield dimensions in virtual pixels.
        target_height_units: aspect2d units the full playfield height maps to
            (2.0 = the full -1..+1 vertical extent of aspect2d).
        sprite_base_scale: the RenderSystem's internal base scale for sprite
            cards (0.5 in the current engine). ``size_to_render_scale`` divides
            this out so a rendered rect's on-screen size matches its pixel size.
    """

    def __init__(
        self,
        width_px: int = 256,
        height_px: int = 240,
        *,
        target_height_units: float = 2.0,
        sprite_base_scale: float = 0.5,
    ) -> None:
        if width_px <= 0 or height_px <= 0:
            raise ValueError("playfield dimensions must be positive")
        if target_height_units <= 0 or sprite_base_scale <= 0:
            raise ValueError("target_height_units and sprite_base_scale must be positive")
        self.width_px = int(width_px)
        self.height_px = int(height_px)
        self.target_height_units = float(target_height_units)
        self.sprite_base_scale = float(sprite_base_scale)

    @property
    def units_per_px(self) -> float:
        """Aspect2d units per virtual pixel (uniform on both axes)."""
        return self.target_height_units / self.height_px

    def to_render(self, x_px: float, y_px: float) -> tuple[float, float]:
        """Convert a pixel-space position to an aspect2d (x, y) position.

        The playfield center maps to (0, 0); pixel (0, 0) is the bottom-left
        corner of the playfield.
        """
        upp = self.units_per_px
        return (
            (float(x_px) - self.width_px / 2.0) * upp,
            (float(y_px) - self.height_px / 2.0) * upp,
        )

    def size_to_render_scale(self, w_px: float, h_px: float) -> tuple[float, float]:
        """Convert a pixel-space size to TransformComponent scale values.

        The returned (scale_x, scale_y) make the RenderSystem's 1x1 card
        (drawn at base_scale * scale) span exactly w_px x h_px playfield
        pixels on screen.
        """
        upp = self.units_per_px
        return (
            float(w_px) * upp / self.sprite_base_scale,
            float(h_px) * upp / self.sprite_base_scale,
        )

    def __repr__(self) -> str:
        return (
            f"VirtualPlayfield({self.width_px}x{self.height_px} px, "
            f"units_per_px={self.units_per_px:.6f})"
        )
