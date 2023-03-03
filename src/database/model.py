"""Declaring data models"""

import sqlalchemy
import sqlalchemy.ext.declarative
from sqlalchemy.orm import relationship

Base = sqlalchemy.ext.declarative.declarative_base()

# pylint: disable=R0903

class World(Base):
    """World representation"""

    __tablename__ = "world"
    world_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    dim_id = sqlalchemy.Column(sqlalchemy.Integer, unique=True)
    chunks = relationship("Chunk", cascade="all,delete", uselist=True, backref="world")

class Chunk(Base):
    """Chunk representation, a 16*256*16 area"""

    __tablename__ = "chunk"
    chunk_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    x_coord = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    z_coord = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    world_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("world.world_id"))
    blocks = relationship("Block", cascade="all,delete", uselist=True, backref="chunk")

class Block(Base):
    """Block representation, coords represent distance inside chunk"""

    __tablename__ = "block"
    block_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    x_coord = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    y_coord = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    z_coord = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    chunk_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("chunk.chunk_id"))
    mc_block_id = sqlalchemy.Column(sqlalchemy.Integer)

class McServer(Base):
    """McServer representation."""

    __tablename__ = "mcserver"
    mcserver_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    uid = sqlalchemy.Column(sqlalchemy.Integer, unique=True, nullable=False)
    path = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String)
    port = sqlalchemy.Column(sqlalchemy.Integer)
    max_players = sqlalchemy.Column(sqlalchemy.Integer)
    ram = sqlalchemy.Column(sqlalchemy.String)
    jar = sqlalchemy.Column(sqlalchemy.String)
    whitelist = sqlalchemy.Column(sqlalchemy.String)
    batchfile = sqlalchemy.Column(sqlalchemy.String)
    javaversion_id = sqlalchemy.Column(sqlalchemy.Integer,
                                       sqlalchemy.ForeignKey("javaversion.javaversion_id"))
    discord = relationship("Discord", cascade="all,delete", uselist=False, backref="mcserver")

class Discord(Base):
    """Discord representation."""

    __tablename__ = "discord"
    discord_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    mcserver_id = sqlalchemy.Column(sqlalchemy.Integer,
                                    sqlalchemy.ForeignKey("mcserver.mcserver_id"))
    active = sqlalchemy.Column(sqlalchemy.Boolean)
    channel_id = sqlalchemy.Column(sqlalchemy.Integer)
    fulllog = sqlalchemy.Column(sqlalchemy.Boolean)

class JavaVersion(Base):
    """Java version representation."""

    __tablename__ = "javaversion"
    javaversion_id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    path = sqlalchemy.Column(sqlalchemy.String, unique=True)
    mcserver = relationship("McServer")
