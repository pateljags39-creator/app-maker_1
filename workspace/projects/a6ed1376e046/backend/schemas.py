from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CalculationBase(BaseModel):
    session_id: str
    expression: str
    result: float


class CalculationCreate(CalculationBase):
    pass


class CalculationResponse(CalculationBase):
    id: UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)