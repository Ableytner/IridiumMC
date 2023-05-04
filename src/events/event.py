from entities.entity import Entity

class Event():
    def __init__(self, caller: Entity) -> None:
        self._caller = caller

    def get_caller(self) -> Entity:
        return self._caller
