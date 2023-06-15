import json

from core import binary_operations
from network.packet import ClientPacket, ServerPacket

class StatusRequest(ClientPacket): # 0x00
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        pass

class StatusResponse(ServerPacket):
    def __init__(self, json_data: dict = None, **kwargs):
        super().__init__(**kwargs)
        self.json = json_data

    def reply(self, writer):
        super().reply(writer, data=binary_operations._encode_varint(0x00) +
                                               binary_operations._encode_string(json.dumps(self.json)))

class PingRequest(ClientPacket): # 0x01
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time = None

    def load(self):
        self.time = binary_operations._decode_long(self.stream)

class PingResponse(ServerPacket):
    def __init__(self, time: int = None, **kwargs):
        super().__init__(**kwargs)
        self.time = time

    def reply(self, writer):
        super().reply(writer, data=binary_operations._encode_varint(0x01) +
                                               binary_operations._encode_long(self.time))

packet_id_map = {
    0x00: StatusRequest,
    0x01: PingRequest
}
