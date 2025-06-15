class GameObject:
    """
    A base class for game objects, which might wrap an ECS entity
    or be used for simpler, non-ECS objects.
    """
    def __init__(self, world, entity=None):
        self.world = world
        self.entity = entity if entity else self.world.create_entity()

    @property
    def id(self):
        return self.entity.id

    def add_component(self, component_instance):
        self.world.add_component(self.id, component_instance)

    def get_component(self, component_type):
        return self.world.get_component(self.id, component_type)

    def remove_component(self, component_type):
        self.world.remove_component(self.id, component_type)

    def update(self, dt):
        """
        Game objects can have their own update logic if needed,
        or this can be handled purely by systems.
        """
        pass
