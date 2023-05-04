from entities.player import PlayerEntity
from events.event import Event

class PlayerJoinEvent(Event):
    def __init__(self, caller: PlayerEntity) -> None:
        super().__init__(caller)
