from fastapi import FastAPI, Depends, APIRouter, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import uvicorn

from database import engine, Base, get_db
from models import Analyst, Recommendation, CompanyMetrics, ReportMetadata
import schemas

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Stock Analyst Analyzer MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")

def seed_database(db: Session):
    """Seed the database with initial mock data for the MVP if empty."""
    if db.query(Analyst).first():
        return

    # Seed Analyst
    analyst = Analyst(
        name="Elena Rostova", 
        firm="Quantum Capital Research", 
        score=4.9, 
        score_type="Accuracy Rating"
    )
    db.add(analyst)
    db.commit()
    db.refresh(analyst)

    # Seed Recommendations
    recs = [
        Recommendation(analyst_id=analyst.id, ticker="NVDA", asset_type="Stock", call_type="Strong Buy"),
        Recommendation(analyst_id=analyst.id, ticker="AMD", asset_type="Stock", call_type="Buy"),
        Recommendation(analyst_id=analyst.id, ticker="INTC", asset_type="Stock", call_type="Sell"),
    ]
    db.add_all(recs)

    # Seed Company Metrics
    metrics = [
        CompanyMetrics(ticker="NVDA", solvency_score=9.8, debt_to_equity=0.4, current_ratio=3.5, free_cash_flow=27000.0),
        CompanyMetrics(ticker="AMD", solvency_score=8.5, debt_to_equity=0.5, current_ratio=2.4, free_cash_flow=3100.0),
        CompanyMetrics(ticker="INTC", solvency_score=5.2, debt_to_equity=1.2, current_ratio=1.2, free_cash_flow=-2000.0),
    ]
    db.add_all(metrics)

    # Seed Metadata
    meta = ReportMetadata(
        universe_size=4200,
        scanned_count=350,
        valid_calls=3,
        source_status="Simulated Data",
        limitations="MVP uses static seeded data for demonstration. Real-time API integration required for live data.",
        is_curated_fallback=True
    )
    db.add(meta)
    db.commit()

@router.get("/report")
def get_report(
    sector: str = Query(default="Technology"),
    market: str = Query(default="US"),
    db: Session = Depends(get_db)
):
    """
    Fetch analyst details, up to 5 recommendations, company metrics, 
    and report metadata based on sector and market filters.
    """
    seed_database(db)
    
    # For MVP purposes, we return the seeded data regardless of the filter,
    # but in a production app, we would filter by sector and market here.
    analyst = db.query(Analyst).first()
    recommendations = db.query(Recommendation).filter(Recommendation.analyst_id == analyst.id).limit(5).all()
    
    tickers = [r.ticker for r in recommendations]
    company_metrics = db.query(CompanyMetrics).filter(CompanyMetrics.ticker.in_(tickers)).all()
    
    report_metadata = db.query(ReportMetadata).first()
    
    return {
        "analyst": analyst,
        "recommendations": recommendations,
        "company_metrics": company_metrics,
        "metadata": report_metadata
    }

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)