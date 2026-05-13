from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from database import Base


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    expression = Column(String, nullable=False)
    result = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Calculation(id={self.id}, session_id='{self.session_id}', expression='{self.expression}', result='{self.result}', timestamp='{self.timestamp}')>"