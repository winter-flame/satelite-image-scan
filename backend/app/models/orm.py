"""SQLAlchemy ORM models."""
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="uploaded")
    created_at = Column(DateTime, server_default=func.now())
