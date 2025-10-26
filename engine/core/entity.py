import uuid

class Entity:
    """
    A simple entity class, represented by a unique ID.
    """
    def __init__(self, name=None):
        self.id = uuid.uuid4()
        self.name = name or f"entity_{self.id}"

    def __repr__(self):
        return f"Entity({self.name}, {self.id})"
