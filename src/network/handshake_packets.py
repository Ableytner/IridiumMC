from core import binary_operations
from network import packet

DEFAULT_PROTOCOL_VERSION = 5

class Handshake(packet.ClientPacket):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.protocol_version = binary_operations._decode_varint(self.stream)
        self.address = binary_operations._decode_string(self.stream)
        self.port = binary_operations._decode_unsigned_short(self.stream)
        self.next_state = binary_operations._decode_varint(self.stream)

    def is_login_next(self):
        return self.next_state == 2

    def is_status_next(self):
        return self.next_state == 1
