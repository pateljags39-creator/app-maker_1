from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Analyst(Base):
    __tablename__ = "analysts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    firm = Column(String)
    score = Column(Float)
    score_type = Column(String)

    recommendations = relationship("Recommendation", back_populates="analyst", cascade="all, delete-orphan")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    analyst_id = Column(Integer, ForeignKey("analysts.id"))
    ticker = Column(String, index=True)
    asset_type = Column(String)
    call_type = Column(String)

    analyst = relationship("Analyst", back_populates="recommendations")


class CompanyMetrics(Base):
    __tablename__ = "company_metrics"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, unique=True, index=True)
    solvency_score = Column(Float)
    debt_to_equity = Column(Float)
    current_ratio = Column(Float)
    free_cash_flow = Column(Float)


class ReportMetadata(Base):
    __tablename__ = "report_metadata"

    id = Column(Integer, primary_key=True, index=True)
    universe_size = Column(Integer)
    scanned_count = Column(Integer)
    valid_calls = Column(Integer)
    source_status = Column(String)
    limitations = Column(String)
    is_curated_fallback = Column(Boolean, default=False)