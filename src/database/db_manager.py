"""Module for managing the database"""

# pylint: disable=E0401, R0402

import logging
from threading import Lock
from typing import List

import sqlalchemy
from sqlalchemy.orm import scoped_session, sessionmaker

import core.instances as instances
from database.model import Base, McServer, Discord, JavaVersion
from dataclass.mcserver import McServer as McServerObj

# pylint: disable=R0801

class DBManager():
    """Class that manages the database"""

    def __init__(self):
        if instances.DB_MANAGER is not None:
            logging.error("There can only be one instance at a time")

        logging.debug("Creating DBManager instance")

        db_connection = sqlalchemy.create_engine("sqlite:///database.db",
                                                 connect_args={'check_same_thread': False})
        Base.metadata.create_all(db_connection)

        session_factory = sessionmaker(db_connection, autoflush=False)
        _session = scoped_session(session_factory)
        self.session = _session()

        self.lock = Lock()

        instances.DB_MANAGER = self

    def add_mcserver(self, mcserver_obj: McServerObj) -> None:
        """Add a McServer object to the database"""

        with self.lock:
            logging.debug(f"Adding server {mcserver_obj.name} " +
                          f"with uid {mcserver_obj.uid} to the database")
            discord = Discord(active=mcserver_obj.dc_active, channel_id=mcserver_obj.dc_id,
                              fulllog=mcserver_obj.dc_full)
            new_mcserver = McServer(uid=mcserver_obj.uid, path=mcserver_obj.path,
                                    name=mcserver_obj.name, port=mcserver_obj.port,
                                    max_players=mcserver_obj.max_players, ram=mcserver_obj.ram,
                                    jar=mcserver_obj.jar, whitelist=mcserver_obj.whitelist,
                                    batchfile=mcserver_obj.batchfile, discord=discord)
            java_version = self.session.query(JavaVersion).filter(JavaVersion.javaversion_id==1) \
                                                          .first()
            java_version.mcserver.append(new_mcserver)
            self.session.add(discord)
            self.session.add(new_mcserver)

        self.commit()

    def add_javaversion(self, name: str, path: str) -> None:
        """Add a javaversion to the database"""

        with self.lock:
            if name in self.session.query(JavaVersion.name).all():
                logging.warn(f"Tried adding javaversion {name} " +
                             f"from {path} to the database, but it already exists")
                return

            logging.debug(f"Adding javaversion {name} " +
                          f"from {path} to the database")

            java_db = self.session.query(JavaVersion).filter(JavaVersion.path==path).first()
            if java_db is not None:
                java_db.name = name
            else:
                new_javaversion = JavaVersion(name=name, path=path)
                self.session.add(new_javaversion)

        self.commit()

    def commit(self) -> None:
        """Commits changes to database"""

        with self.lock:
            try:
                self.session.commit()
            except sqlalchemy.exc.IntegrityError:
                logging.debug("Committing database changes failed, rolling back")
                self.session.rollback()

    def get_javaname(self, path) -> str:
        """Return the javaversion with the given path"""

        with self.lock:
            saved = self.session.query(JavaVersion).filter(JavaVersion.path==path).first()
            if saved is None:
                logging.warn(f"Tried getting JavaVersion from {path}, " +
                             f"but it doesn't exist")
                raise KeyError(f"JavaVersion database entry with path '{path}' can't be found")
            return saved.name

    def get_javaversion(self, name) -> str:
        """Return the javaversion with the given name"""

        with self.lock:
            saved = self.session.query(JavaVersion).filter(JavaVersion.name==name).first()
            if saved is None:
                raise KeyError(f"JavaVersion database entry with name '{name}' can't be found")
            return saved.path

    def get_javaversions(self) -> list[tuple[str, str]]:
        """Return all javaversions"""

        with self.lock:
            return [(item.name, item.path) for item in self.session.query(JavaVersion).all()]

    def get_mcserver(self, uid: int) -> McServerObj:
        """Return the server with the given UID"""

        with self.lock:
            saved = self.session.query(McServer).filter(McServer.uid==uid).first()
            if saved is None:
                raise KeyError(f"McServer database entry with uid '{uid}' can't be found")
            java_obj = self.session.query(JavaVersion) \
                           .filter(JavaVersion.javaversion_id==saved.javaversion_id).first()
            if java_obj is None:
                java_obj = self.session.query(JavaVersion).filter(JavaVersion.javaversion_id==1) \
                               .first()
            return McServerObj(uid=saved.uid, name=saved.name, path=saved.path, port=saved.port,
                               max_players=saved.max_players, ram=saved.ram, jar=saved.jar,
                               whitelist=saved.whitelist, batchfile=saved.batchfile,
                               javapath=java_obj.path, dc_active=saved.discord.active,
                               dc_id=saved.discord.channel_id, dc_full=saved.discord.fulllog)

    def get_mcserver_by_name(self, name: str) -> McServerObj:
        """Return the server with the given name"""

        with self.lock:
            saved = self.session.query(McServer).filter(McServer.name==name).first()
            if saved is None:
                raise KeyError(f"McServer database entry with name '{name}' can't be found")
            return saved

    def get_mcservers(self) -> List[McServerObj]:
        """Returns all McServer objects in the database"""

        with self.lock:
            saved = self.session.query(McServer).all()
            ret_list = []
            if saved != []:
                for item in saved:
                    java_obj = self.session.query(JavaVersion) \
                                   .filter(JavaVersion.javaversion_id==item.javaversion_id).first()
                    if java_obj is None:
                        java_obj = self.session.query(JavaVersion) \
                                       .filter(JavaVersion.javaversion_id==1).first()
                    if java_obj is not None:
                        ret_list.append(McServerObj(item.uid, item.name, item.path, item.port,
                                                    item.max_players, item.ram, item.jar,
                                                    item.whitelist, item.batchfile, java_obj.path,
                                                    item.discord.active, item.discord.channel_id,
                                                    item.discord.fulllog))
        return ret_list

    def get_number_of_mcservers(self) -> int:
        """Returns the number of McServer objects in the database"""

        return self.session.query(McServer).count()

    def get_new_uid(self) -> int:
        """Return a new, unused UID"""

        if self.get_number_of_mcservers() == 0:
            return 1
        last_server = self.session.query(McServer).order_by(McServer.mcserver_id.desc()).first()
        return last_server.mcserver_id + 1

    def remove_mcserver(self, uid: int) -> None:
        """Remove a server from the database"""

        with self.lock:
            logging.debug(f"Removing McServer with uid {uid} from the database")
            uid = self.session.query(McServer).filter(McServer.uid==uid).first().uid
            self.session.query(Discord).filter(Discord.mcserver_id==uid).delete()
            self.session.query(McServer).filter(McServer.uid==uid).delete()
        self.commit()

    def save_mcserver(self, mcserver_obj: McServerObj) -> None:
        """Save a server to the database"""

        with self.lock:
            db_srv: McServer = self.session.query(McServer) \
                                   .filter(McServer.uid==mcserver_obj.uid).first()
            if db_srv is None:
                self.lock.release()
                logging.debug(f"Adding McServer {mcserver_obj.name} " +
                              f"with uid {mcserver_obj.uid} to the database")
                self.add_mcserver(mcserver_obj)
                return
            logging.debug(f"Saving McServer {mcserver_obj.name} " +
                          f"with uid {mcserver_obj.uid} to the database")
            db_srv.name = mcserver_obj.name
            db_srv.path = mcserver_obj.path
            db_srv.port = mcserver_obj.port
            db_srv.jar = mcserver_obj.jar
            db_srv.javaversion_id = self.session.query(JavaVersion) \
                                        .filter(JavaVersion.path==mcserver_obj.javapath) \
                                        .first().javaversion_id
            db_srv.max_players = mcserver_obj.max_players
            db_srv.ram = mcserver_obj.ram
            db_srv.whitelist = mcserver_obj.whitelist
            db_srv.batchfile = mcserver_obj.batchfile
            db_discord: Discord = db_srv.discord
            db_discord.active = mcserver_obj.dc_active
            db_discord.channel_id = mcserver_obj.dc_id
            db_discord.fulllog = mcserver_obj.dc_full
        self.commit()
