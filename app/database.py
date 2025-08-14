"""Database setup for the menu scan backend."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Determine the database URL from environment or fallback to local SQLite.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# SQLite requires special connection arguments when using multithreading.
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy engine and session factory.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our ORM models.
Base = declarative_base()


def get_db():
    """Provide a session generator to be used as a FastAPI dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
