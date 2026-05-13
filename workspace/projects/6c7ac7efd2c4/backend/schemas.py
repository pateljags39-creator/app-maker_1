from pydantic import BaseModel, ConfigDict

class PersistentCalculatorDataBase(BaseModel):
    memory_register: float
    history_log: str # Storing history as a JSON string

class PersistentCalculatorDataCreate(PersistentCalculatorDataBase):
    pass

class PersistentCalculatorData(PersistentCalculatorDataBase):
    id: int

    model_config = ConfigDict(from_attributes=True)