from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .db import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    command = Column(
        String(50), nullable=False
    )  # seed, run, test, build, snapshot, source freshness
    selector = Column(String(255), nullable=True)  # ex: --select tag:staging
    cron = Column(String(100), nullable=False)  # 0 2 * * *
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    runs = relationship("Run", back_populates="job", cascade="all, delete-orphan")


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    trigger = Column(String(20), default="scheduled", nullable=False)  # scheduled | manual
    status = Column(String(20), default="running", nullable=False)  # running | success | failed
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    return_code = Column(Integer, nullable=True)
    log_path = Column(String(500), nullable=True)
    command_line = Column(Text, nullable=True)

    job = relationship("Job", back_populates="runs")
