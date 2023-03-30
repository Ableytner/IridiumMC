import logging
import random
from time import sleep
import uuid
from socket import socket

from core import binary_operations
from core.readable_buffer import ReadableBuffer
from network import packet, handshake_packets, status_packets, login_packets, play_packets, client_packets

STATUS_STATE = 1
LOGIN_STATE = 2

class MinecraftProtocol():
    _transport = None

    def __init__(self, request: socket):
        self.socket = request

    def read_packet(self, packet_class=None) -> packet.Packet | int:
        packet_length = binary_operations._decode_varint(self.socket)
        packet_data = self.socket.recv(packet_length)
        packet_stream = ReadableBuffer(packet_data)
        packet_id = binary_operations._decode_varint(packet_stream)

        if packet_class is None:
            if packet_id not in client_packets.packet_id_map.keys():
                return packet_id
            packet_class = client_packets.packet_id_map[packet_id]

        logging.debug("Loading packet class: {}".format(packet_class))
        packet = packet_class(data=packet_data, stream=packet_stream)
        packet.load()
        return packet

    def write_packet(self, packet):
        packet.reply(self.socket)

    def get_status(self, address, port):
        conn = handshake_packets.HandshakePacket(address=address,
                               port=port,
                               next_state=STATUS_STATE)
        self.write_packet(conn)
        self.write_packet(status_packets.StatusRequestPacket())
        status_response = self.read_packet(status_packets.StatusResponsePacket)
        return status_response.json

    def handle_status(self, status_json: dict):
        self.read_packet(status_packets.StatusRequestPacket)
        self.write_packet(status_packets.StatusResponsePacket(status_json))
        conn_info = self.read_packet(status_packets.PingRequestPacket)
        self.write_packet(status_packets.PingResponsePacket(time=conn_info.time))

    def handle_login(self):
        conn_info = self.read_packet(login_packets.LoginStartPacket)
        player_uuid = uuid.uuid4()
        self.write_packet(login_packets.LoginSuccessPacket(conn_info.name, player_uuid))
        self.write_packet(play_packets.JoinGamePacket())
        return (player_uuid, conn_info.name)

    def handle_server_keepalive(self):
        rand_int = random.randint(1, 1000)
        self.write_packet(play_packets.KeepAlivePacket(rand_int))
        conn_info = self.read_packet(play_packets.KeepAlivePacket)
        if rand_int != conn_info.rand_number:
            self.write_packet(play_packets.DisconnectPacket("Timed out"))
