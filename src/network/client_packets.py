from core import binary_operations
from network.packet import Packet

class Player(Packet): # PlayerOnGround
    def __init__(self, on_ground: bool = None, **kwargs):
        super().__init__(**kwargs)
        self.on_ground = on_ground

    async def load(self): # 0x03
        self.on_ground = await binary_operations._decode_boolean(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=binary_operations._encode_varint(0x03) +
                                         binary_operations._encode_boolean(self.on_ground))

class PlayerPosition(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def load(self): # 0x04
        self.x = await binary_operations._decode_double(self.stream)
        self.feety = await binary_operations._decode_double(self.stream)
        self.heady = await binary_operations._decode_double(self.stream)
        self.z = await binary_operations._decode_double(self.stream)
        self.on_ground = await binary_operations._decode_boolean(self.stream)

class PlayerLook(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def load(self): # 0x05
        self.yaw = await binary_operations._decode_float(self.stream)
        self.pitch = await binary_operations._decode_float(self.stream)
        self.on_ground = await binary_operations._decode_boolean(self.stream)

class PlayerPositionAndLook(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def load(self): # 0x06
        self.x = await binary_operations._decode_double(self.stream)
        self.feety = await binary_operations._decode_double(self.stream)
        self.heady = await binary_operations._decode_double(self.stream)
        self.z = await binary_operations._decode_double(self.stream)
        self.yaw = await binary_operations._decode_float(self.stream)
        self.pitch = await binary_operations._decode_float(self.stream)
        self.on_ground = await binary_operations._decode_boolean(self.stream)

class ClientSettingsPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def load(self): # 0x15
        self.locale = await binary_operations._decode_string(self.stream)
        self.view_distance = await binary_operations._decode_byte(self.stream)
        self.chat_flags = await binary_operations._decode_byte(self.stream)
        self.chat_colors = await binary_operations._decode_boolean(self.stream)
        self.difficulty = await binary_operations._decode_byte(self.stream)
        self.show_cape = await binary_operations._decode_boolean(self.stream)

class PluginMessagePacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def load(self): # 0x17
        self.channel = await binary_operations._decode_string(self.stream)
        self.length = await binary_operations._decode_short(self.stream)
        self.data = await binary_operations._decode_bytearray(self.stream, self.length)

packet_id_map = {
    0x03: Player,
    0x04: PlayerPosition,
    0x05: PlayerLook,
    0x06: PlayerPositionAndLook,
    0x15: ClientSettingsPacket,
    0x17: PluginMessagePacket
}
