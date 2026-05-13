from sqlalchemy import Column, Integer, Float, String
from database import Base

class PersistentCalculatorData(Base):
    __tablename__ = "calculator_data"

    id = Column(Integer, primary_key=True, index=True)
    memory_register = Column(Float, default=0.0)
    history_log = Column(String, default="[]") # Stores a JSON string of history entries