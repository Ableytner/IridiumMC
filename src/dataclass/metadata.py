from __future__ import annotations
from dataclasses import dataclass

from core import binary_operations

STOP_BYTE = binary_operations._encode_byte(127)

@dataclass
class Entity():
    on_fire: bool = None
    crouched: bool = None
    sprinting: bool = None
    eating: bool = None
    invisible: bool = None
    air_ka: int = None

    def to_bytes(self) -> bytes:
        ret_data = b""
        if False: # !!! needs implementation !!!
            ret_data += binary_operations._encode_metakey(0, 0) # byte
            ret_data += binary_operations._encode_byte(0)
        if self.air_ka is not None:
            ret_data += binary_operations._encode_metakey(1, 1) # short
            ret_data += binary_operations._encode_short(0) # Air?
        return ret_data

@dataclass
class LivingEntity(Entity):
    health: float = None
    potion_effect_color: int = None
    is_potion_effect_ambient: bool = None
    number_of_arrows_in_entity: int = None
    name_tag: str = None
    always_show_name_tag: bool = None

    def to_bytes(self) -> bytes:
        ret_data = super().to_bytes()
        if self.health is not None:
            ret_data += binary_operations._encode_metakey(6, 3) # float
            ret_data += binary_operations._encode_float(self.health)
        if self.potion_effect_color is not None:
            ret_data += binary_operations._encode_metakey(7, 2) # int
            ret_data += binary_operations._encode_int(self.potion_effect_color)
        if self.number_of_arrows_in_entity is not None:
            ret_data += binary_operations._encode_metakey(8, 0) # byte
            ret_data += binary_operations._encode_byte(int(self.is_potion_effect_ambient))
        if self.name_tag is not None:
            ret_data += binary_operations._encode_metakey(10, 4) # string
            ret_data += binary_operations._encode_string(self.name_tag)
        if self.always_show_name_tag is not None:
            ret_data += binary_operations._encode_metakey(11, 0) # byte
            ret_data += binary_operations._encode_byte(int(self.always_show_name_tag))
        return ret_data

@dataclass
class Human(LivingEntity):
    unknown_field: int = None
    absorption_hearts: float = None
    score: int = None

    def to_bytes(self) -> bytes:
        ret_data = super().to_bytes()
        if self.unknown_field is not None:
            ret_data += binary_operations._encode_metakey(16, 0) # byte
            ret_data += binary_operations._encode_byte(self.unknown_field)
        if self.absorption_hearts is not None:
            ret_data += binary_operations._encode_metakey(17, 3) # float
            ret_data += binary_operations._encode_float(self.absorption_hearts)
        if self.score is not None:
            ret_data += binary_operations._encode_metakey(18, 2) # int
            ret_data += binary_operations._encode_int(self.score)
        return ret_data
