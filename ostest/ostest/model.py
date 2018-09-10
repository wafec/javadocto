from sqlalchemy import Column, Boolean, String, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from ostest import config

Base = declarative_base()
CONF = config.CONF

class Service(Base):
    __tablename__ = "service"

    id = Column(String(64), primary_key=True)
    type = Column(String(255))
    enabled = Column(Boolean)
    extra = Column(String)

class Endpoint(Base):
    __tablename__ = "endpoint"

    id = Column(String(64), primary_key=True)
    url = Column(String)
    service_id = Column(String(64), ForeignKey('service.id'))
    service = relationship(Service)
    enabled = Column(Boolean)

class EndpointBkp(Base):
    __tablename__ = "endpoint_bkp"

    id = Column(Integer, primary_key=True)
    endpoint_id = Column(String(64), ForeignKey('endpoint.id'))
    endpoint = relationship(Endpoint)
    url = Column(String)


engine = create_engine(CONF.database.connection_string)
DBSession = sessionmaker(bind=engine)