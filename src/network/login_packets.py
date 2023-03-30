from core import binary_operations
from network.packet import Packet

class LoginStartPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = None

    def load(self):
        self.name = binary_operations._decode_string(self.stream)

class LoginSuccessPacket(Packet):
    def __init__(self, name, uuid, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.player_uuid = uuid

    def reply(self, writer, data=None):
        super().reply(writer, data=binary_operations._encode_varint(0x02) +
                                         binary_operations._encode_string(str(self.player_uuid)) + # binary_operations._encode_varint(len(player_uuid.bytes)) + binary_operations._encode_uuid(player_uuid) +
                                         binary_operations._encode_string(self.name))
