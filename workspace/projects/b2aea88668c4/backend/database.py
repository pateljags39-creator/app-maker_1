from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite database URL. The database file will be created in the same directory as the script.
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# Create the SQLAlchemy engine.
# For SQLite, 'check_same_thread=False' is needed to allow multiple threads to interact with the database,
# which is common in web applications like FastAPI where requests are handled in different threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a SessionLocal class.
# This class will be an instance of Session configured to connect to our engine.
# Each instance of SessionLocal will be a database session.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare the Base class.
# This is the base class that our SQLAlchemy models will inherit from.
# It provides the declarative mapping features.
Base = declarative_base()

# Dependency to get a database session.
# This function can be used in FastAPI path operations to inject a DB session.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()