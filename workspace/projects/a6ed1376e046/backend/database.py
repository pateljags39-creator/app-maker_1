from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# Create the SQLAlchemy engine
# connect_args is needed for SQLite when using multiple threads/requests
# as it's not designed for concurrent writes without specific handling.
# For a simple local app, check_same_thread=False is common.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session.
# The `autocommit=False` means that changes are not committed automatically.
# The `autoflush=False` means that objects are not flushed to the database automatically.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare a Base class for our ORM models
# This is the base class that our SQLAlchemy models will inherit from.
Base = declarative_base()