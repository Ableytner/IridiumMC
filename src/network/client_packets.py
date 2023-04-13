import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dataclass.player import Player
    from core.iridium_server import IridiumServer

from dataclass.position import Position
from network import handshake_packets, client_packets, server_packets
from core import binary_operations
from network.packet import ClientPacket

class KeepAlive(ClientPacket): # 0x00
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.keep_alive_id = binary_operations._decode_int(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        if self.keep_alive_id == player.keepalive[2]:
            player.keepalive[0] = 0 # switch to WAITING
            player.keepalive[1] = server.TPS * 5 # wait for 5 seconds until next keepalive
            player.keepalive[2] = 0
        else:
            # client sent back the wrong keepalive_id
            server.disconnect_player(player, "KeepAliveID is incorrect")

class ChatMessage(ClientPacket): # 0x01
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.message = binary_operations._decode_string(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        logging.info(f"[{player.name}] {self.message}")
        for pl in server.players.values():
            pl.mcprot.write_packet(server_packets.ChatMesage(f"[{player.name}] {self.message}"))

class Player(ClientPacket):  # 0x03 PlayerOnGround
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        player.on_ground = self.on_ground

class PlayerPosition(ClientPacket): # 0x04
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.x = binary_operations._decode_double(self.stream)
        self.feety = binary_operations._decode_double(self.stream)
        self.heady = binary_operations._decode_double(self.stream)
        self.z = binary_operations._decode_double(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        player.pos = Position(self.x, self.heady, self.z)
        player.on_ground = self.on_ground

class PlayerLook(ClientPacket): # 0x05
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.yaw = binary_operations._decode_float(self.stream)
        self.pitch = binary_operations._decode_float(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        player.rot = (self.yaw, self.pitch)
        player.on_ground = self.on_ground

class PlayerPositionAndLook(ClientPacket): # 0x06
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.x = binary_operations._decode_double(self.stream)
        self.feety = binary_operations._decode_double(self.stream)
        self.heady = binary_operations._decode_double(self.stream)
        self.z = binary_operations._decode_double(self.stream)
        self.yaw = binary_operations._decode_float(self.stream)
        self.pitch = binary_operations._decode_float(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        player.pos = Position(self.x, self.heady, self.z)
        player.rot = (self.yaw, self.pitch)
        player.on_ground = self.on_ground

class ClientSettings(ClientPacket): # 0x15
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.locale = binary_operations._decode_string(self.stream)
        self.view_distance = binary_operations._decode_byte(self.stream)
        self.chat_flags = binary_operations._decode_byte(self.stream)
        self.chat_colors = binary_operations._decode_boolean(self.stream)
        self.difficulty = binary_operations._decode_byte(self.stream)
        self.show_cape = binary_operations._decode_boolean(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        pass

class PluginMessage(ClientPacket): # 0x17
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.channel = binary_operations._decode_string(self.stream)
        self.length = binary_operations._decode_short(self.stream)
        self.data = binary_operations._decode_bytearray(self.stream, self.length)

    def process(self, server: "IridiumServer", player: "Player"):
        pass

class Animation(ClientPacket): # 0x0A
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.entity_id = binary_operations._decode_int(self.stream)
        self.animation_id = binary_operations._decode_byte(self.stream)
        # 0: No animation
        # 1: Swing arm
        # 2: Damage animation
        # 3: Leave bed
        # 5: Eat food
        # 6: Critical effect
        # 7: Magic critical effect
        # 102: (unknown)
        # 104: Crouch
        # 105: Uncrouch

    def process(self, server: "IridiumServer", player: "Player"):
        pass

class EntityAction(ClientPacket): # 0x0B
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.entity_id = binary_operations._decode_int(self.stream)
        self.action_id = binary_operations._decode_byte(self.stream)
        self.jump_boost = binary_operations._decode_int(self.stream)

    def process(self, server: "IridiumServer", player: "Player"):
        pass

packet_id_map = {
    0x00: KeepAlive,
    0x01: ChatMessage,
    0x03: Player,
    0x04: PlayerPosition,
    0x05: PlayerLook,
    0x06: PlayerPositionAndLook,
    0x15: ClientSettings,
    0x17: PluginMessage,
    0x0A: Animation,
    0x0B: EntityAction
}
