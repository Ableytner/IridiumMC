from core import binary_operations
from network.packet import Packet

class Player(Packet): # PlayerOnGround
    def __init__(self, on_ground: bool = None, **kwargs):
        super().__init__(**kwargs)
        self.on_ground = on_ground

    def load(self): # 0x03
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def reply(self, socket, data=None):
        super().reply(socket, data=binary_operations._encode_varint(0x03) +
                                         binary_operations._encode_boolean(self.on_ground))

class PlayerPosition(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self): # 0x04
        self.x = binary_operations._decode_double(self.stream)
        self.feety = binary_operations._decode_double(self.stream)
        self.heady = binary_operations._decode_double(self.stream)
        self.z = binary_operations._decode_double(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

class PlayerLook(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self): # 0x05
        self.yaw = binary_operations._decode_float(self.stream)
        self.pitch = binary_operations._decode_float(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

class PlayerPositionAndLook(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self): # 0x06
        self.x = binary_operations._decode_double(self.stream)
        self.feety = binary_operations._decode_double(self.stream)
        self.heady = binary_operations._decode_double(self.stream)
        self.z = binary_operations._decode_double(self.stream)
        self.yaw = binary_operations._decode_float(self.stream)
        self.pitch = binary_operations._decode_float(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

class ClientSettingsPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self): # 0x15
        self.locale = binary_operations._decode_string(self.stream)
        self.view_distance = binary_operations._decode_byte(self.stream)
        self.chat_flags = binary_operations._decode_byte(self.stream)
        self.chat_colors = binary_operations._decode_boolean(self.stream)
        self.difficulty = binary_operations._decode_byte(self.stream)
        self.show_cape = binary_operations._decode_boolean(self.stream)

class PluginMessagePacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self): # 0x17
        self.channel = binary_operations._decode_string(self.stream)
        self.length = binary_operations._decode_short(self.stream)
        self.data = binary_operations._decode_bytearray(self.stream, self.length)

packet_id_map = {
    0x03: Player,
    0x04: PlayerPosition,
    0x05: PlayerLook,
    0x06: PlayerPositionAndLook,
    0x15: ClientSettingsPacket,
    0x17: PluginMessagePacket
}
