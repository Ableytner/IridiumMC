from entities.player_entity import PlayerEntity
from events.event import Event

class PlayerJoinEvent(Event):
    def __init__(self, player: PlayerEntity) -> None:
        self.player = player
