from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

@dataclass
class InputBinding:
    """
    Defines a specific input that can trigger a named action.
    An action in InputComponent can have multiple InputBindings.
    """
    input_type: Literal["key", "mouse_button", "gamepad_button", "gamepad_axis"]
    
    # For key, mouse_button, gamepad_button: Panda3D event name (e.g., "arrow_left", "mouse1", "gamepad-face_a")
    # For gamepad_axis: A string identifier for the axis (e.g., "lstick_x", "rtrigger")
    # These will be mapped to Panda3D's Gamepad.Axis enums in the InputSystem.
    event_name: str 
    
    # For gamepad_axis: The value the axis must exceed (absolute) to be considered active.
    axis_threshold: float = 0.5 
    
    # For gamepad_axis: Specifies which direction of axis movement triggers the action.
    # "positive": e.g., right on x-axis, down on y-axis (depending on Panda3D conventions)
    # "negative": e.g., left on x-axis, up on y-axis
    # "any":      e.g., if lstick_x is <-0.5 or >0.5 (useful if mapping an entire axis to one "active" state)
    #             Note: If "any", the InputSystem will typically report it as active if abs(value) > threshold.
    #             For more precise positive/negative triggering, use "positive" or "negative".
    axis_direction: Literal["positive", "negative", "any"] = "positive"

    # Optional: Specify a particular gamepad ID (integer index). 
    # If None, the binding applies to any connected gamepad that provides the event/axis.
    gamepad_id: int | None = None

    def __post_init__(self):
        if self.input_type != "gamepad_axis":
            # Ensure threshold and direction are not inadvertently set for non-axis types
            # where they don't apply, to avoid confusion.
            # Or, one might choose to allow them but document they are ignored.
            # For now, let's be strict.
            if self.axis_threshold != 0.5 or self.axis_direction != "positive": # default values
                # This check is a bit crude if defaults change. A better way might be to have them as None initially.
                # For simplicity, we'll rely on users not setting them for non-axis types.
                pass
        if self.input_type == "gamepad_axis" and self.event_name not in ["lstick_x", "lstick_y", "rstick_x", "rstick_y", "ltrigger", "rtrigger"]:
            print(f"Warning: Gamepad axis event_name '{self.event_name}' may not be standard. Supported: lstick_x, lstick_y, rstick_x, rstick_y, ltrigger, rtrigger")

