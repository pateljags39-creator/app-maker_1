import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Define the path for the SQLite database file
# The database file will be created in the same directory as the script.
DATABASE_FILE = "./app.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DATABASE_FILE}"

# Create the SQLAlchemy engine
# connect_args={"check_same_thread": False} is needed for SQLite when using multiple threads,
# which FastAPI might do.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
# The 'autocommit=False' means that the session will not commit changes automatically.
# The 'autoflush=False' means that changes will not be flushed to the database automatically.
# The 'bind=engine' connects the session to the database engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare Base for declarative models
# This Base will be inherited by all SQLAlchemy models.
Base = declarative_base()

# Dependency to get a database session
def get_db():
    """
    Returns a database session.

    This function is intended to be used with FastAPI's Depends system.
    It creates a new session, yields it, and ensures it's closed afterwards.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()