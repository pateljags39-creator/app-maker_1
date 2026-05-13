from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite when using multiple threads,
# which FastAPI might do.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
# The `autocommit=False` and `autoflush=False` settings ensure that changes are not
# committed automatically and are not flushed to the database until explicitly told to.
# `bind=engine` connects this session to our database engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our models
# This is the base class that our SQLAlchemy models will inherit from.
# It's crucial that this is declared only once and imported by all models.
Base = declarative_base()

# Dependency to get a database session
# This function can be used with FastAPI's Depends to manage database sessions.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()