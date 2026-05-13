from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from typing import List, Optional

# Analyst Schemas
class AnalystBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    name: str
    firm: str
    score: float
    score_type: str

class AnalystCreate(AnalystBase):
    pass

class Analyst(AnalystBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Recommendation Schemas
class RecommendationBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    analyst_id: int
    ticker: str
    asset_type: str
    call_type: str

class RecommendationCreate(RecommendationBase):
    pass

class Recommendation(RecommendationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Company Metrics Schemas
class CompanyMetricsBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    ticker: str
    solvency_score: float
    debt_to_equity: float
    current_ratio: float
    free_cash_flow: float

class CompanyMetricsCreate(CompanyMetricsBase):
    pass

class CompanyMetrics(CompanyMetricsBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Report Metadata Schemas
class ReportMetadataBase(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    universe_size: int
    scanned_count: int
    valid_calls: int
    source_status: str
    limitations: str
    is_curated_fallback: bool

class ReportMetadataCreate(ReportMetadataBase):
    pass

class ReportMetadata(ReportMetadataBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# Composite Response Schema for the Report Endpoint
class ReportResponse(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)
    analyst: Optional[Analyst] = None
    recommendations: List[Recommendation] = []
    company_metrics: List[CompanyMetrics] = []
    metadata: Optional[ReportMetadata] = None