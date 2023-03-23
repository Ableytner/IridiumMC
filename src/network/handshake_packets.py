from core import binary_operations
from network.packet import Packet

DEFAULT_PROTOCOL_VERSION = 5

class HandshakePacket(Packet):
    def __init__(self, address=None, port=None, next_state=None, **kwargs):
        super().__init__(**kwargs)
        self.address = address
        self.port = port
        self.next_state = next_state
        self.protocol_version = DEFAULT_PROTOCOL_VERSION

    def load(self):
        self.protocol_version = binary_operations._decode_varint(self.stream)
        self.address = binary_operations._decode_string(self.stream)
        self.port = binary_operations._decode_unsigned_short(self.stream)
        self.next_state = binary_operations._decode_varint(self.stream)

    def reply(self, writer, data=None):
        super().reply(writer, data=binary_operations._encode_varint(0x00) +
                                               binary_operations._encode_varint(self.protocol_version) +
                                               binary_operations._encode_string(self.address) +
                                               binary_operations._encode_unsigned_short(self.port) +
                                               binary_operations._encode_varint(self.next_state))

    def is_login_next(self):
        return self.next_state == 2

    def is_status_next(self):
        return self.next_state == 1
