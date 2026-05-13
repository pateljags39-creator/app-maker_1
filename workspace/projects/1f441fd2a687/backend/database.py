from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite when used with multiple threads,
# which FastAPI might do. StaticPool is used to ensure a single connection for SQLite.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
# The `autocommit=False` and `autoflush=False` settings are standard.
# `bind=engine` connects this sessionmaker to our engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
# This is where declarative_base() is called ONCE.
Base = declarative_base()

# Dependency to get a database session
def get_db():
    """
    Dependency function that provides a SQLAlchemy session.
    It ensures the session is closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()