import asyncio
import logging
import time
import traceback
import os
from datetime import datetime
from time import sleep
from threading import Thread, Event

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
        self.exit = False
        self.world = World(0)
        self.players: dict[str, Player] = {}

    async def run_server(self):
        logging.info(f"IridiumMC server starting on port {self.port}")
        self.server = await asyncio.start_server(self._handle_client, host="192.168.0.154", port=self.port)

        logging.info("creating world...")
        wg = WorldGenerator("flat", self.world)
        wg.generate_start_region(Position(0, 0, 0))
        logging.info(f"done")

        asyncio.get_event_loop().create_task(self.mainloop())

    async def mainloop(self):
        while True:
            start_time = datetime.now()

            for player in self.players.values():
                while not player.network_in.empty():
                    conn_info = player.network_in.get()
                    if isinstance(conn_info, client_packets.Player):
                        player.on_ground = conn_info.on_ground
                    if isinstance(conn_info, client_packets.PlayerPosition):
                        player.pos = Position(conn_info.x, conn_info.heady, conn_info.z)
                        player.on_ground = conn_info.on_ground
                    if isinstance(conn_info, client_packets.PlayerPositionAndLook):
                        player.pos = Position(conn_info.x, conn_info.heady, conn_info.z)
                        player.rot = (conn_info.yaw, conn_info.pitch)
                        player.on_ground = conn_info.on_ground
                    if isinstance(conn_info, client_packets.Player) or isinstance(conn_info, client_packets.PlayerPosition) or isinstance(conn_info, client_packets.PlayerPositionAndLook):
                        await player.mcprot.write_packet(play_packets.PlayerPositionAndLook(player.pos, player.rot, player.on_ground))
                        logging.info(player)

            sleep_time = (1 / TPS) - (datetime.now() - start_time).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    def get_status(self):
        retr_time = time.time()
        status = {
            "online": False,
            "host": "ableytner.ddns.net",
            "port": self.port,
            "eula_blocked": False,
            "retrieved_at": int(retr_time),
            "expires_at": int(retr_time) + 6000,
            "version": {
                "name_raw": "1.7.10",
                "name_clean": "1.7.10",
                "name_html": "<span><span style=\"color: #ffffff;\">1.7.10</span></span>",
                "protocol": 5
            },
            "players": {
                "online": 0,
                "max": 20,
                "list": []
            },
            "motd": {
                "raw": "IridiumMC server!",
                "clean": "IridiumMC server!",
                "html": "<span><span style=\"color: #ffffff;\">IridiumMC server! </span>"
            },
            "icon": None,
            "mods": [],
        }
        return status

    async def _handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        logging.debug("Client connected!")

        mcprot = MinecraftProtocol(client_reader, client_writer)
        conn_info = await mcprot.read_packet(handshake_packets.HandshakePacket)

        if conn_info.is_status_next():
            await mcprot.handle_status(self.get_status())
            return
        elif conn_info.is_login_next():
            uuid, name = await mcprot.handle_login()
            player = Player(uuid, name, Position(0, 10, 0), (0, 0), False, mcprot)
            logging.info(f"{name} joined the game")

            try:
                await player.mcprot.write_packet(play_packets.PlayerPositionAndLook(player.pos, player.rot, player.on_ground))
                logging.debug("Generating chunk data...")
                chunk_gen_start_time = datetime.now()
                for x in range(-1, 2):
                    for z in range(-1, 2):
                        chunk_data = self.world.to_packet_data(x, z)
                        await player.mcprot.write_packet(play_packets.MapChunkBulkPacket(*chunk_data))
                logging.debug(f"Done, took {round((datetime.now() - chunk_gen_start_time).total_seconds(), 2)}s")
            except Exception:
                print(traceback.format_exc())
        else:
            logging.exception(f"unknown next_state {conn_info.next_state}")
            return
        
        self.players[str(uuid)] = player
        Thread(target=player.network_func, daemon=True).start()
