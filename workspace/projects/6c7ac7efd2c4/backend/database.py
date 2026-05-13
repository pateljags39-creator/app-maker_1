from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Define the database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# Create the SQLAlchemy engine
# The `connect_args={"check_same_thread": False}` is required for SQLite when
# using it with multiple threads, which FastAPI does.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
# The 'autocommit=False' means that the session will not commit until explicitly told to.
# The 'autoflush=False' means that the session will not flush until explicitly told to.
# 'bind=engine' connects the session to the engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for our declarative models
# All SQLAlchemy models will inherit from this Base.
# This ensures that Base is defined only once, as per the rules.
Base = declarative_base()