import json
import uuid

from core import binary_operations
from dataclass.position import Position

DEFAULT_PROTOCOL_VERSION = 47

class Packet:
    def __init__(self, data=None, stream=None):
        self.data = data
        self.stream = stream

    async def load(self):
        raise NotImplementedError()

    async def reply(self, writer, data=None):
        if data is None:
            data = self.data

        writer.write(binary_operations._encode_varint(len(data)))
        writer.write(data)
        await writer.drain()

class HandshakePacket(Packet):
    def __init__(self, address=None, port=None, next_state=None, **kwargs):
        super().__init__(**kwargs)
        self.address = address
        self.port = port
        self.next_state = next_state
        self.protocol_version = DEFAULT_PROTOCOL_VERSION

    async def load(self):
        self.protocol_version = await binary_operations._decode_varint(self.stream)
        self.address = await binary_operations._decode_string(self.stream)
        self.port = await binary_operations._decode_unsigned_short(self.stream)
        self.next_state = await binary_operations._decode_varint(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x00) +
                                               binary_operations._encode_varint(self.protocol_version) +
                                               binary_operations._encode_string(self.address) +
                                               binary_operations._encode_unsigned_short(self.port) +
                                               binary_operations._encode_varint(self.next_state))

    def is_login_next(self):
        return self.next_state == 2

    def is_status_next(self):
        return self.next_state == 1


class StatusRequestPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def load(self):
        pass

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x00))


# noinspection PyAttributeOutsideInit
class StatusResponsePacket(Packet):
    def __init__(self, json_data=None, **kwargs):
        super().__init__(**kwargs)
        self.json = json_data

    async def load(self):
        json_str = await binary_operations._decode_string(self.stream)
        self.json = json.loads(json_str)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x00) +
                                               binary_operations._encode_string(json.dumps(self.json)))

    @property
    def users(self):
        return self.json['players']['online']

    @users.setter
    def users(self, value):
        self.json['players']['online'] = value


class PingRequestPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time = None

    async def load(self):
        self.time = await binary_operations._decode_long(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x01) +
                                               binary_operations._encode_long(self.time))

class PingResponsePacket(Packet):
    def __init__(self, time=None, **kwargs):
        super().__init__(**kwargs)
        self.time = time

    async def load(self):
        self.time = await binary_operations._decode_long(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x01) +
                                               binary_operations._encode_long(self.time))

class LoginStartPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = None

    async def load(self):
        self.name = await binary_operations._decode_string(self.stream)
        # self.has_player_uuid = await binary_operations._decode_boolean(self.stream)
        # if self.has_player_uuid:
        #     self.player_uuid = await binary_operations._decode_uuid(self.stream)

class LoginSuccessPacket(Packet):
    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        self.name = name

    async def reply(self, writer, data=None):
        player_uuid = uuid.uuid4()
        await super().reply(writer, data=binary_operations._encode_varint(0x02) +
                                         binary_operations._encode_string(str(player_uuid)) + # binary_operations._encode_varint(len(player_uuid.bytes)) + binary_operations._encode_uuid(player_uuid) +
                                         binary_operations._encode_string(self.name))

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
    def __init__(self, position: Position, look: tuple[float, float], **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.look = look

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x08) +
                                         binary_operations._encode_double(self.position.x) +
                                         binary_operations._encode_double(self.position.y) +
                                         binary_operations._encode_double(self.position.z) +
                                         binary_operations._encode_float(self.look[0]) + # yaw
                                         binary_operations._encode_float(self.look[1]) + # pitch
                                         binary_operations._encode_boolean(False)) # on the ground

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
