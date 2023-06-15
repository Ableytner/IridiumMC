from dataclass.position import Position
from dataclass.save import World
from blocks import tnt, log

class WorldGenerator():
    def __init__(self, level_type, world: World) -> None:
        self._level_type = level_type
        self._world = world
    
    @property
    def world(self) -> World:
        return self._world

    def generate_start_region(self, position: Position):
        for x in range(-(4*16), 4*16, 16):
            for z in range(-(4*16), 4*16, 16):
                self.generate_chunk_column(((position.x//16) * 16) + x, ((position.z//16) * 16) + z)

    def generate_chunk_column(self, start_pos_x: int, start_pos_z):
        # already generated
        if self.world.chunk_exists(start_pos_x//16, start_pos_z//16):
            return

        if self._level_type == "flat":
            for y in range(256):
                for x in range(16):
                    for z in range(16):
                        if (y) <= 5:
                            block_pos = Position(start_pos_x + x, y, start_pos_z + z)
                            self.world.set_block(block_pos, log.Log())
