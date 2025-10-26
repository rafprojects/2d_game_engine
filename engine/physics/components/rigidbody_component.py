from panda3d.core import Vec2

from engine.core.component import Component

class RigidBodyComponent(Component):
    """
    Component for physics simulation.
    Handles velocity, acceleration, and physical properties.
    """
    
    def __init__(self,
                 velocity: Vec2 = Vec2(0, 0),
                 acceleration: Vec2 = Vec2(0, 0),
                 mass: float = 1.0,
                 drag: float = 0.0,
                 gravity_scale: float = 1.0,
                 is_kinematic: bool = False,
                 is_static: bool = False):
        """
        Initialize a rigidbody component.
        
        Args:
            velocity: Current velocity (units/second)
            acceleration: Current acceleration (units/second²)
            mass: Mass of the object (affects collision response)
            drag: Air resistance (0 = no drag, 1 = stops immediately)
            gravity_scale: Multiplier for global gravity (0 = no gravity)
            is_kinematic: If True, not affected by physics forces but can move via code
            is_static: If True, never moves (infinite mass effectively)
        """
        self.velocity = velocity
        self.acceleration = acceleration
        self.mass = mass
        self.drag = drag
        self.gravity_scale = gravity_scale
        self.is_kinematic = is_kinematic
        self.is_static = is_static
        
        # Forces applied this frame (reset each frame)
        self.forces = Vec2(0, 0)
        
    def add_force(self, force: Vec2):
        """Add a force to be applied this frame."""
        if not self.is_static:
            self.forces += force
    
    def add_impulse(self, impulse: Vec2):
        """Add an instantaneous velocity change."""
        if not self.is_static:
            self.velocity += impulse / self.mass
    
    def update_physics(self, dt: float, gravity: Vec2 = Vec2(0, 0)):
        """
        Update physics for this rigidbody.
        
        Args:
            dt: Delta time
            gravity: Global gravity vector
        """
        if self.is_static:
            return
        
        if not self.is_kinematic:
            # Apply gravity
            if self.gravity_scale > 0:
                self.add_force(gravity * self.mass * self.gravity_scale)
            
            # Calculate acceleration from forces
            if self.mass > 0:
                self.acceleration = self.forces / self.mass
            
            # Apply acceleration to velocity
            self.velocity += self.acceleration * dt
            
            # Apply drag
            if self.drag > 0:
                drag_force = self.velocity * self.drag
                self.velocity -= drag_force * dt
        
        # Reset forces for next frame
        self.forces = Vec2(0, 0)
