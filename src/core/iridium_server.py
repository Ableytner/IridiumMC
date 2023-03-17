import asyncio
import logging
import time
import traceback
import os
import datetime
from time import sleep
from threading import Thread

from network import handshake_packets, play_packets
from network.protocol import MinecraftProtocol
from core.worldgen import WorldGenerator
from dataclass.save import World
from dataclass.position import Position
from dataclass.player import Player
from network.network_handler import NetworkHandler

class IridiumServer():
    def __init__(self, port: int, path: str) -> None:
        self.port = port
        self.path = path
        self.server = None
        self.exit = False
        self.world = World(0)
        self.players: dict[str, Player] = {}
        self.network_thread = Thread(target=self.network_noasync, daemon=True)

    TPS = 20

    async def run_server(self):
        def handle_client_task(client_reader, client_writer):
            asyncio.run_coroutine_threadsafe(self._handle_client(client_reader=client_reader,
                                             client_writer=client_writer), asyncio.get_event_loop())

        logging.info(f"IridiumMC server starting on port {self.port}")
        self.server = await asyncio.start_server(handle_client_task, host="192.168.0.154", port=self.port)

        self.network_thread.start()

        logging.info("creating world...")
        wg = WorldGenerator("flat", self.world)
        wg.generate_start_region(Position(0, 0, 0))
        logging.info(f"done")

    def network_noasync(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(NetworkHandler(self).mainloop())
        loop.close()

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
            player = Player(uuid, name, Position(0, 0, 0), mcprot)
            logging.info(f"{name} joined the game")

            try:
                await player.mcprot.write_packet(play_packets.PlayerPositionAndLook(Position(0, 10, 0), (0, 0)))
                logging.debug("Generating chunk data...")
                chunk_gen_start_time = datetime.datetime.now()
                for x in range(-1, 2):
                    for z in range(-1, 2):
                        chunk_data = self.world.to_packet_data(x, z)
                        await player.mcprot.write_packet(play_packets.MapChunkBulkPacket(*chunk_data))
                logging.debug(f"Done, took {round((datetime.datetime.now() - chunk_gen_start_time).total_seconds(), 2)}s")
            except Exception:
                print(traceback.format_exc())
        else:
            logging.exception(f"unknown next_state {conn_info.next_state}")
            return
        
        self.players[str(uuid)] = player
