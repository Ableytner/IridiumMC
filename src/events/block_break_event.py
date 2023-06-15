from entities.player_entity import PlayerEntity
from blocks.block import Block
from events.event import Event
from dataclass.position import Position

class BlockBreakEvent(Event):
    def __init__(self, player: PlayerEntity, block: Block, position: Position) -> None:
        self.player = player
        self.block = block
        self.position = position
