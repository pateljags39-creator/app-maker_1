from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CalculationBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    session_id: str
    expression: str
    result: float


class CalculationCreate(CalculationBase):
    pass


class CalculationResponse(CalculationBase):
    id: UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)