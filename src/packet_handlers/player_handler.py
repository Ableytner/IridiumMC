from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.iridium_server import IridiumServer
from network import handshake_packets, play_packets, client_packets
from dataclass.player import Player
from dataclass.position import Position

def player(server: "IridiumServer", player: Player, conn_info: client_packets.Player):
    player.on_ground = conn_info.on_ground

def player_position(server: "IridiumServer", player: Player, conn_info: client_packets.PlayerPosition):
    player.pos = Position(conn_info.x, conn_info.heady, conn_info.z)
    player.on_ground = conn_info.on_ground

def player_position_and_look(server: "IridiumServer", player: Player, conn_info: client_packets.PlayerPositionAndLook):
    player.pos = Position(conn_info.x, conn_info.heady, conn_info.z)
    player.rot = (conn_info.yaw, conn_info.pitch)
    player.on_ground = conn_info.on_ground
