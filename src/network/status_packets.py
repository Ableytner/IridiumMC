import json

from core import binary_operations
from network.packet import Packet

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
