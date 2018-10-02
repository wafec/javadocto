from sqlalchemy import Column, Boolean, String, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from ostest import config

Base = declarative_base()
CONF = config.CONF


class EndpointBackup(Base):
    __tablename__ = "endpoint_backup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(String(64))
    endpoint_url = Column(String)
    reference_url = Column(String)


engine = create_engine(CONF.database.connection_string)
DBSession = sessionmaker(bind=engine)