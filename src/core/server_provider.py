from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.iridium_server import IridiumServer

_iridium_server = None

def get() -> "IridiumServer":
    return _iridium_server
