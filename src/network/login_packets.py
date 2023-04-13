from core import binary_operations
from network import packet

class LoginStart(packet.ClientPacket):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = None

    def load(self):
        self.name = binary_operations._decode_string(self.stream)

class LoginSuccess(packet.ServerPacket):
    def __init__(self, name, uuid, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.player_uuid = uuid

    def reply(self, writer):
        super().reply(writer, data=binary_operations._encode_varint(0x02) +
                                         binary_operations._encode_string(str(self.player_uuid)) +
                                         binary_operations._encode_string(self.name))
