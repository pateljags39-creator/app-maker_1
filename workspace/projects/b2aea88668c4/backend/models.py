import datetime

from sqlalchemy import Column, Integer, String, DateTime
from database import Base


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    body = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)