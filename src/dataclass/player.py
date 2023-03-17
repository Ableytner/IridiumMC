import uuid
from dataclasses import dataclass

from dataclass.position import Position
from network.protocol import MinecraftProtocol

@dataclass
class Player():
    uuid: uuid.UUID
    name: str
    pos: Position
    rot: tuple[float, float]
    on_ground: bool
    mcprot: MinecraftProtocol

    def __str__(self) -> str:
        return f"uuid={self.uuid}, name={self.name}, pos={self.pos}, rot={self.rot}, on_ground={self.on_ground}"
