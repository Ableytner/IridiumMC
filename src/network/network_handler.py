from datetime import datetime
from time import sleep

from network import play_packets
from dataclass.player import Player

class NetworkHandler():
    def __init__(self, server) -> None:
        self.server = server

    async def mainloop(self):
        while True:
            start_time = datetime.now()

            c = 0
            while c < len(self.server.players.values()):
                sleep(5)
                player: Player = list(self.server.players.values())[c]
                await player.mcprot.write_packet(play_packets.DisconnectPacket("disconn."))
                self.server.players.pop(str(player.uuid))
            
            sleep_time = (1 / self.server.TPS) - (datetime.now() - start_time).total_seconds()
            if sleep_time > 0:
                sleep(sleep_time)
