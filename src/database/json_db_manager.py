import json
import logging
import os

from dataclass.save import World, Chunk
from dataclass.position import Position
from blocks import block, log, tnt

SAVEPATH = "server/world.json"

def save_world(world: World) -> None:
    storage = {}
    for chunkx, d in world.chunk_columns.items():
        for chunkz, chunk_column in d.items():
            for chunky, chunk in chunk_column.chunks.items():
                _save_chunk(storage, chunk, chunkx*16, chunky*16, chunkz*16)

    os.rename(SAVEPATH, SAVEPATH + ".backup")
    with open(SAVEPATH, "w+") as file:
        json.dump(storage, file)
    os.remove(SAVEPATH + ".backup")

def load_world() -> World:
    world = World(0)

    if not os.path.isfile(SAVEPATH):
        # if a backup exists, load it
        if not os.path.isfile(SAVEPATH + ".backup"):
            with open(SAVEPATH, "w+") as file:
                file.write("{}")
            return world
        else:
            os.rename(SAVEPATH + ".backup", SAVEPATH)

    try:
        with open(SAVEPATH, "r") as file:
            storage: dict = json.load(file)
    except Exception as e:
        logging.error(str(e))
        if os.path.isfile(SAVEPATH + ".backup"):
            # remove the broken save and try again with the backup
            logging.info("Backup found, retrying...")
            os.remove(SAVEPATH)
            return load_world()

    for x, r1 in storage.items():
        for y, r2 in r1.items():
            for z, stored_block in r2.items():
                block_obj = _json_to_block(stored_block)
                if block_obj is not None:
                    pos = Position(int(x), int(y), int(z))
                    world.set_block(pos, block_obj)
    
    return world

def _save_chunk(storage: dict, chunk: Chunk, dx: int, dy: int, dz: int) -> None:
    for encstr, block_obj in chunk.blocks.items():
        pos = chunk._encstr_to_pos(encstr)
        pos = Position(pos.x + dx, pos.y + dy, pos.z + dz)
        if not pos.x in storage.keys():
            storage[pos.x] = {}
        if not pos.y in storage[pos.x].keys():
            storage[pos.x][pos.y] = {}
        storage[pos.x][pos.y][pos.z] = _block_to_json(block_obj)

def _block_to_json(block_obj: block.Block) -> dict:
    stored = {"id": block_obj.block_id}
    return stored

def _json_to_block(stored: dict) -> block.Block | None:
    block_id = stored["id"]
    block_obj = None

    if block_id == 17:
        block_obj = log.Log()
    elif block_id == 46:
        block_obj = tnt.TNT()
    
    return block_obj
