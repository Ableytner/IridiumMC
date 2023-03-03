import json
import uuid

from core import binary_operations

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
        await super().reply(writer, data=binary_operations._encode_varint(0) +
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
        await super().reply(writer, data=binary_operations._encode_varint(0))


# noinspection PyAttributeOutsideInit
class StatusResponsePacket(Packet):
    def __init__(self, json_data=None, **kwargs):
        super().__init__(**kwargs)
        self.json = json_data

    async def load(self):
        json_str = await binary_operations._decode_string(self.stream)
        self.json = json.loads(json_str)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0) +
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
        await super().reply(writer, data=binary_operations._encode_varint(1) +
                                               binary_operations._encode_long(self.time))


class PingResponsePacket(Packet):
    def __init__(self, time=None, **kwargs):
        super().__init__(**kwargs)
        self.time = time

    async def load(self):
        self.time = await binary_operations._decode_long(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(1) +
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
        await super().reply(writer, data=binary_operations._encode_varint(2) +
                                         binary_operations._encode_string(str(player_uuid)) + # binary_operations._encode_varint(len(player_uuid.bytes)) + binary_operations._encode_uuid(player_uuid) +
                                         binary_operations._encode_string(self.name))

class LoginPlayPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(1) +
                                         binary_operations._encode_varint(-1) + # player entity id
                                         binary_operations._encode_unsigned_byte(0) + # gamemode, 0=survival, 1=creative
                                         binary_operations._encode_byte(0) + # dimension, -1=nether, 0=overworld, 1=end
                                         binary_operations._encode_unsigned_byte(0) + # difficulty, 0=peaceful
                                         binary_operations._encode_unsigned_byte(5) + # max players
                                         binary_operations._encode_string("flat")) # level type

class ChunkDataPacket(Packet):
    def __init__(self, chunk_data_len: int=0, chunk_data: bytes=b"", **kwargs):
        super().__init__(**kwargs)
        self.chunk_data_len = chunk_data_len
        self.chunk_data = chunk_data

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(21) +
                                         binary_operations._encode_int(0) + # chunk x coord
                                         binary_operations._encode_int(0) + # chunk z coord
                                         binary_operations._encode_boolean(True) +
                                         binary_operations._encode_unsigned_short(0b1111111111111111) + #0b0000000000000001 # bitmap representing which chunk data is included, 0=all air, 1=include data
                                         binary_operations._encode_unsigned_short(0) +
                                         binary_operations._encode_int(self.chunk_data_len) + # compressed chunk data size
                                         self.chunk_data)