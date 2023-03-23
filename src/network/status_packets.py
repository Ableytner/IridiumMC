import json

from core import binary_operations
from network.packet import Packet

class StatusRequestPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        pass

    def reply(self, writer, data=None):
        super().reply(writer, data=binary_operations._encode_varint(0x00))


# noinspection PyAttributeOutsideInit
class StatusResponsePacket(Packet):
    def __init__(self, json_data: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.json = json_data

    def load(self):
        json_str = binary_operations._decode_string(self.stream)
        self.json = json.loads(json_str)

    def reply(self, writer, data=None):
        super().reply(writer, data=binary_operations._encode_varint(0x00) +
                                               binary_operations._encode_string(json.dumps(self.json)))

    @property
    def users(self):
        return self.json['players']['online']

    @users.setter
    def users(self, value):
        self.json['players']['online'] = value


class PingRequestPacket(Packet): # 0x01
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time = None

    def load(self):
        self.time = binary_operations._decode_long(self.stream)

class PingResponsePacket(Packet):
    def __init__(self, time: int = None, **kwargs):
        super().__init__(**kwargs)
        self.time = time

    def reply(self, writer, data=None):
        super().reply(writer, data=binary_operations._encode_varint(0x01) +
                                               binary_operations._encode_long(self.time))
