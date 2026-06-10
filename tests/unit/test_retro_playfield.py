"""Tests for engine.retro.playfield.VirtualPlayfield (P2-D re-work support).

The playfield is the single source of truth for mapping virtual retro pixels
to the RenderSystem's aspect2d coordinates. These tests pin the exact
arithmetic so that "visual size == collision size" stays true by construction.
"""

import pytest

from engine.retro.playfield import VirtualPlayfield


def test_default_mapping_center_and_corners():
    pf = VirtualPlayfield()  # 256x240
    assert pf.units_per_px == pytest.approx(2.0 / 240)

    # Playfield center maps to screen center.
    assert pf.to_render(128, 120) == pytest.approx((0.0, 0.0))

    # Bottom-left corner.
    x, y = pf.to_render(0, 0)
    assert x == pytest.approx(-128 * 2.0 / 240)  # ~ -1.0667
    assert y == pytest.approx(-1.0)

    # Top-right corner.
    x, y = pf.to_render(256, 240)
    assert x == pytest.approx(128 * 2.0 / 240)
    assert y == pytest.approx(1.0)


def test_size_round_trips_through_render_base_scale():
    """scale * base_scale (0.5) must reproduce the requested pixel size."""
    pf = VirtualPlayfield()
    sx, sy = pf.size_to_render_scale(12, 16)

    # What the RenderSystem actually draws: 1x1 card * base_scale * scale.
    drawn_w_units = 0.5 * sx
    drawn_h_units = 0.5 * sy

    # Convert back to pixels.
    assert drawn_w_units / pf.units_per_px == pytest.approx(12.0)
    assert drawn_h_units / pf.units_per_px == pytest.approx(16.0)


def test_custom_playfield_and_validation():
    pf = VirtualPlayfield(320, 200, target_height_units=1.0)
    assert pf.units_per_px == pytest.approx(1.0 / 200)
    assert pf.to_render(160, 100) == pytest.approx((0.0, 0.0))

    with pytest.raises(ValueError):
        VirtualPlayfield(0, 240)
    with pytest.raises(ValueError):
        VirtualPlayfield(256, 240, sprite_base_scale=0)
