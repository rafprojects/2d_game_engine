import uuid

class Entity:
    """
    A simple entity class, represented by a unique ID.
    """
    def __init__(self):
        self.id = uuid.uuid4()

    def __repr__(self):
        return f"Entity({self.id})"
