from __future__ import annotations
from collections import defaultdict
import zlib
from dataclasses import dataclass, field

from dataclass.position import Position
from core import binary_operations

@dataclass
class Block():
    pos: Position
    block_id: int

    @property
    def chunk_pos(self) -> Position:
        return Position(self.pos.x % 16, self.pos.y, self.pos.z % 16)

    @staticmethod
    def air() -> Block:
        return Block(Position(0, 0, 0), 0)

@dataclass
class Chunk():
    x: int
    z: int
    blocks: dict[int, dict[int, dict[int, Block|None]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(dict)))

    def to_packet_data(self) -> tuple[int, bytes]:
        data = b""
        i = 0

        block_type = []
        block_metadata = []
        block_light = []
        sky_light = []
        add = []
        biome = []

        for chunk_c in range(16):
            for y in range(chunk_c, chunk_c + 16):
                for z in range(16):
                    for x in range(16):
                        try:
                            block = self.blocks[x][y][z]
                        except KeyError:
                            block = Block.air()

                        data += binary_operations._encode_unsigned_byte(block.block_id)
                        data += binary_operations._encode_unsigned_byte(0b00001000)
                        data += binary_operations._encode_unsigned_byte(0b11110000)
                        i += 1

                        block_type.append(binary_operations._encode_byte(block.block_id))
                        block_metadata.append(0b0000)
                        block_light.append(0b1000)
                        sky_light.append(0b1111)
                        add.append(0b0000)
                    biome.append(binary_operations._encode_byte(1))

        for block_data in [block_type, block_metadata, block_light, sky_light, add, biome]:
            pass
            # temp_data = b"".join(block_data)
            # data += binary_operations._encode_varint(len(block_data)) + temp_data

        zlibbed_str = zlib.compress(data)
        compressed_string = zlibbed_str[2:-4]
        return i, compressed_string

@dataclass
class World():
    dim_id: int
    chunks: dict[int, dict[int, Chunk|None]] = field(default_factory=lambda: defaultdict(dict))
