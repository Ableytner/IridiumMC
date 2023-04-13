from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Position():
    x: float
    y: float
    z: float

    def dist_to(self, pos2: Position) -> float:
        dx = abs(self.x - pos2.x)
        dy = abs(self.y - pos2.y)
        dz = abs(self.z - pos2.z)
        return dx + dy + dz

    def dist_to_horizontal(self, pos2: Position) -> float:
        dx = abs(self.x - pos2.x)
        dz = abs(self.z - pos2.z)
        return dx + dz
