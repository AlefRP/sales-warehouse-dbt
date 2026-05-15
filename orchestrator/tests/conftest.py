"""Test fixtures.

Sets env vars before importing the app so config/db pick up the test sandbox
instead of the production defaults (/data/logs, sqlite at /data/...).
"""
import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="orch_test_"))
os.environ.setdefault("ORCHESTRATOR_DB_URL", f"sqlite:///{(_TMP / 'test.db').as_posix()}")
os.environ.setdefault("ORCHESTRATOR_LOGS_DIR", str(_TMP / "logs"))
os.environ.setdefault("DBT_PROJECT_DIR", str(_TMP))
os.environ.setdefault("DBT_PROFILES_DIR", str(_TMP))
os.environ.setdefault("DBT_TARGET", "dev")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from orchestrator.app import db as app_db  # noqa: E402
from orchestrator.app import scheduler as app_sched  # noqa: E402
from orchestrator.app.db import Base, get_session  # noqa: E402
from orchestrator.app.main import app  # noqa: E402


@pytest.fixture
def db_session(monkeypatch):
    """Fresh in-memory SQLite for each test, isolated via dependency override."""
    # StaticPool keeps a single connection so all queries see the same
    # :memory: database (otherwise each connection gets its own empty DB).
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(app_db, "engine", engine)
    monkeypatch.setattr(app_db, "SessionLocal", TestingSession)
    monkeypatch.setattr(app_sched, "SessionLocal", TestingSession)

    session = TestingSession()

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_session] = _override
    try:
        yield session
    finally:
        session.close()
        app.dependency_overrides.clear()
        engine.dispose()


@pytest.fixture
def client(db_session, monkeypatch):
    """TestClient that does NOT trigger lifespan (no APScheduler in tests)."""
    monkeypatch.setattr(app_sched, "add_or_update", lambda _job: None)
    monkeypatch.setattr(app_sched, "remove", lambda _job: None)
    monkeypatch.setattr(app_sched, "next_run_time", lambda _job: None)
    return TestClient(app)


@pytest.fixture
def fake_trigger_run(monkeypatch):
    """Stub trigger_run so we don't actually fork a dbt subprocess."""
    calls: list[tuple[int, str]] = []

    def _stub(job_id: int, trigger: str = "scheduled") -> int:
        calls.append((job_id, trigger))
        from orchestrator.app.models import Run
        from orchestrator.app.db import SessionLocal
        s = SessionLocal()
        try:
            run = Run(job_id=job_id, trigger=trigger, status="running")
            s.add(run)
            s.commit()
            return run.id
        finally:
            s.close()

    monkeypatch.setattr("orchestrator.app.routes.jobs.trigger_run", _stub)
    return calls
