from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# Create the SQLAlchemy engine
# connect_args is needed for SQLite to allow multiple threads to access the same connection
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class
# Each instance of SessionLocal will be a database session
# The `autocommit=False` and `autoflush=False` settings ensure that changes are not
# committed until explicitly told to, and that objects are not flushed to the database
# until a commit or explicit flush.
# `bind=engine` connects this sessionmaker to our engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare the Base class for our SQLAlchemy models
# This Base class will be inherited by all our ORM models.
Base = declarative_base()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()