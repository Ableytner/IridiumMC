import logging
import sys
import os
import base64
from datetime import datetime
from time import sleep
from threading import Thread
from socket import socket
from socketserver import ThreadingTCPServer

from network import handshake_packets, play_packets, client_packets
from network.protocol import MinecraftProtocol
from core.worldgen import WorldGenerator
from dataclass.save import World
from dataclass.position import Position
from dataclass.player import Player

TPS = 20

class IridiumServer():
    def __init__(self, port: int, path: str) -> None:
        self.port = port
        self.path = path
        self.server = None
        self.world = World(0)
        self.players: dict[str, Player] = {}
        IridiumServer.inst = self

    inst = None

    def run_server(self):
        logging.info(f"IridiumMC server starting on port {self.port}")
        self.server = ThreadingTCPServer(("0.0.0.0", self.port), self.handle_client_connect)

        logging.info("creating world...")
        wg = WorldGenerator("flat", self.world)
        wg.generate_start_region(Position(0, 0, 0))
        logging.info(f"done")

        Thread(target=self.mainloop, daemon=True).start()
        self.server.serve_forever()

    def mainloop(self):
        while True:
            start_time = datetime.now()

            for player in self.players.values():
                player.keepalive[1] -= 1
                if player.keepalive[1] <= 0:
                    if player.keepalive[0] == 0:
                        # send keepalive to client
                        player.keepalive[0] = 1
                        player.keepalive[1] = TPS * 5 # wait for 5 seconds to receive back keepalive
                        ka_packet = play_packets.KeepAlivePacket()
                        player.mcprot.write_packet(ka_packet)
                        player.keepalive[2] = ka_packet.keep_alive_id

                while not player.network_in.empty():
                    conn_info = player.network_in.get()
                    if isinstance(conn_info, client_packets.KeepAlivePacket):
                        if conn_info.keep_alive_id == player.keepalive[2]:
                            player.keepalive[0] = 0
                            player.keepalive[1] = TPS * 5 # wait for 5 seconds until next keepalive
                            player.keepalive[2] = 0
                        else:
                            player.mcprot.write_packet(play_packets.DisconnectPacket("KeepAliveID is incorrect"))
                    if isinstance(conn_info, client_packets.Player):
                        player.on_ground = conn_info.on_ground
                    if isinstance(conn_info, client_packets.PlayerPosition):
                        player.pos = Position(conn_info.x, conn_info.heady, conn_info.z)
                        player.on_ground = conn_info.on_ground
                    if isinstance(conn_info, client_packets.PlayerPositionAndLook):
                        player.pos = Position(conn_info.x, conn_info.heady, conn_info.z)
                        player.rot = (conn_info.yaw, conn_info.pitch)
                        player.on_ground = conn_info.on_ground

            sleep_time = (1 / TPS) - (datetime.now() - start_time).total_seconds()
            if sleep_time > 0:
                sleep(sleep_time)

    @staticmethod
    def handle_client_connect(request: socket, client_address: tuple[str, int], server: ThreadingTCPServer) -> None:
        self = IridiumServer.inst
        logging.debug("Client connected!")

        mcprot = MinecraftProtocol(request)
        conn_info = mcprot.read_packet(handshake_packets.HandshakePacket)

        if conn_info.is_status_next():
            mcprot.handle_status(self.get_status())
            return
        elif conn_info.is_login_next():
            uuid, name = mcprot.handle_login()
            player = Player(self, uuid, name, Position(0, 10, 0), (0, 0), False, mcprot)
            logging.info(f"{name} joined the game")

            player.mcprot.write_packet(play_packets.PlayerPositionAndLook(player.pos, player.rot, player.on_ground))
            logging.debug("Generating chunk data...")
            chunk_gen_start_time = datetime.now()
            for x in range(-1, 2):
                for z in range(-1, 2):
                    chunk_data = self.world.to_packet_data(x, z)
                    player.mcprot.write_packet(play_packets.MapChunkBulkPacket(*chunk_data))
            logging.debug(f"Done, took {round((datetime.now() - chunk_gen_start_time).total_seconds(), 2)}s")
        else:
            logging.exception(f"unknown next_state {conn_info.next_state}")
            return

        self.players[str(uuid)] = player
        player.network_func()

    def disconnect_player(self, player: Player, reason: str):
        player.mcprot.write_packet(play_packets.DisconnectPacket(reason))
        self.players.pop(str(player.uuid))

    def get_status(self) -> dict:
        image_path = "server/server-icon.png"
        dataurl = None
        if os.path.isfile(image_path):
            with open(image_path, "rb") as fb:
                binary_fc = fb.read()
            base64_utf8_str = base64.b64encode(binary_fc).decode('utf-8')
            file_ext = image_path.split('.')[-1]
            dataurl = f'data:image/{file_ext};base64,{base64_utf8_str}'

        status = {
            "version": {
                "name": "1.7.10",
                "protocol": handshake_packets.DEFAULT_PROTOCOL_VERSION
            },
            "players": {
                "max": 20,
                "online": len(self.players),
                "sample": []
            },
            "description": {
                "text": f"IridiumMC server! - Running with Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}!"
            },
            "favicon": dataurl or ""
        }
        return status
