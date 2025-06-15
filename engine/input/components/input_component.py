from dataclasses import dataclass, field
from typing import Dict, List

from engine.core.component import Component
from engine.input.input_bindings import InputBinding

@dataclass
class InputComponent(Component):
    """
    Component to manage input actions for an entity.

    Attributes:
        action_bindings (Dict[str, List[InputBinding]]): Maps action names (e.g., 'move_left')
                                                       to a list of InputBinding objects.
                                                       This allows an action to be triggered by multiple inputs
                                                       (e.g., 'arrow_left' key OR gamepad d-pad left).
        action_active (Dict[str, bool]): Stores whether an action is currently active (pressed).
                                         Updated by the InputSystem.
        action_just_pressed (Dict[str, bool]): Stores whether an action was just pressed in the current frame.
                                               Updated by the InputSystem.
        action_just_released (Dict[str, bool]): Stores whether an action was just released in the current frame.
                                                Updated by the InputSystem.
        # Internal state for tracking previous frame's active state, used by InputSystem
        _previous_action_active (Dict[str, bool]): Stores the active state from the previous frame.
                                                  This is managed by the InputSystem.
    """
    action_bindings: Dict[str, List[InputBinding]] = field(default_factory=dict)
    action_active: Dict[str, bool] = field(default_factory=dict, init=False)
    action_just_pressed: Dict[str, bool] = field(default_factory=dict, init=False)
    action_just_released: Dict[str, bool] = field(default_factory=dict, init=False)
    _previous_action_active: Dict[str, bool] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        # Initialize action states based on action_bindings keys
        for action_name in self.action_bindings:
            self.action_active[action_name] = False
            self.action_just_pressed[action_name] = False
            self.action_just_released[action_name] = False
            self._previous_action_active[action_name] = False
