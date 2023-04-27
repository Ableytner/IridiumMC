from entities.entity import Entity

class TileEntity(Entity):
    """Blocks with extra functionality"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
