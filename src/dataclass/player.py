import uuid
from dataclasses import dataclass

from dataclass.position import Position
from network.protocol import MinecraftProtocol

@dataclass
class Player():
    uuid: uuid.UUID
    name: str
    pos: Position
    mcprot: MinecraftProtocol
