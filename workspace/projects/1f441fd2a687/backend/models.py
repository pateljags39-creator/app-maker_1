import uuid
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.sql import func

from database import Base


class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, index=True, nullable=False)
    expression = Column(String, nullable=False)
    result = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Calculation(id='{self.id}', session_id='{self.session_id}', expression='{self.expression}', result={self.result}, timestamp='{self.timestamp}')>"