from datetime import datetime
from pydantic import BaseModel, ConfigDict

class CalculationBase(BaseModel):
    session_id: str
    expression: str
    result: str

class CalculationCreate(CalculationBase):
    # No additional fields needed for creation beyond base
    pass

class CalculationResponse(CalculationBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)