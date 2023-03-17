import json
import uuid
import random

from core import binary_operations
from dataclass.position import Position
from network.packet import Packet

packet_id_map: dict

class JoinGamePacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x01) +
                                         binary_operations._encode_int(-1) + # player entity id
                                         binary_operations._encode_unsigned_byte(0) + # gamemode, 0=survival, 1=creative
                                         binary_operations._encode_byte(0) + # dimension, -1=nether, 0=overworld, 1=end
                                         binary_operations._encode_unsigned_byte(0) + # difficulty, 0=peaceful
                                         binary_operations._encode_unsigned_byte(5) + # max players
                                         binary_operations._encode_string("default")) # level type

class PlayerPositionAndLook(Packet):
    def __init__(self, position: Position, look: tuple[float, float], on_ground: bool, **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.look = look
        self.on_ground = on_ground

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x08) +
                                         binary_operations._encode_double(self.position.x) +
                                         binary_operations._encode_double(self.position.y) +
                                         binary_operations._encode_double(self.position.z) +
                                         binary_operations._encode_float(self.look[0]) + # yaw
                                         binary_operations._encode_float(self.look[1]) + # pitch
                                         binary_operations._encode_boolean(self.on_ground))

class SpawnPositionPacket(Packet):
    def __init__(self, position: Position, **kwargs):
        super().__init__(**kwargs)
        self.position = position

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x05) +
                                         binary_operations._encode_int(self.position.x) +
                                         binary_operations._encode_int(self.position.y) +
                                         binary_operations._encode_int(self.position.z))

class MapChunkBulkPacket(Packet):
    def __init__(self, chunk_column_count: int, data_len: int, sky_light: bool, data: bytes, metadata: bytes, **kwargs):
        super().__init__(**kwargs)
        self.chunk_column_count = chunk_column_count
        self.data_len = data_len
        self.sky_light = sky_light
        self.data = data
        self.metadata = metadata

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x26) +
                                         binary_operations._encode_short(self.chunk_column_count) +
                                         binary_operations._encode_int(self.data_len) +
                                         binary_operations._encode_boolean(self.sky_light) +
                                         self.data +
                                         self.metadata)

class KeepAlivePacket(Packet):
    def __init__(self, rand_number: None, **kwargs):
        super().__init__(**kwargs)
        if rand_number is None:
            rand_number = random.randint(1, 1000)
        self.rand_number = rand_number

    async def load(self):
        self.rand_number = await binary_operations._decode_int(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x00) +
                                         binary_operations._encode_int(self.rand_number))

class DisconnectPacket(Packet):
    def __init__(self, reason: str, **kwargs):
        super().__init__(**kwargs)
        self.reason = reason

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x40) +
                                         binary_operations._encode_string(self.reason))
