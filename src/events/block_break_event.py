from entities.player_entity import PlayerEntity
from blocks.block import Block
from events.event import Event

class BlockBreakEvent(Event):
    def __init__(self, player: PlayerEntity, block: Block) -> None:
        self.player = player
        self.block = block
