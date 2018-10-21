from sqlalchemy import Column, Boolean, String, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
import os


Base = declarative_base()


class EndpointBackup(Base):
    __tablename__ = "endpoint_backup"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint_id = Column(String(64))
    endpoint_url = Column(String)
    reference_url = Column(String)


engine = create_engine(os.environ['SPY_CONNECTION_STRING'])
DBSession = sessionmaker(bind=engine)