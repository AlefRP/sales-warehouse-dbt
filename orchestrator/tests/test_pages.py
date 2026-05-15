from datetime import datetime

from orchestrator.app.models import Job, Run
from orchestrator.app.routes.pages import _stats


def _make_job(session, **kw):
    job = Job(name=kw.get("name", "j"), command="build", cron="* * * * *",
              is_active=kw.get("is_active", True))
    session.add(job)
    session.commit()
    return job


def _make_run(session, job_id, status="success"):
    r = Run(job_id=job_id, trigger="manual", status=status, started_at=datetime.utcnow())
    session.add(r)
    session.commit()
    return r


class TestHealthz:
    def test_healthz_ok(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert "time" in body


class TestStats:
    def test_empty_db(self, db_session):
        stats = _stats(db_session)
        assert stats["total_jobs"] == 0
        assert stats["success_rate"] is None

    def test_success_rate_computed(self, db_session):
        job = _make_job(db_session)
        _make_run(db_session, job.id, "success")
        _make_run(db_session, job.id, "success")
        _make_run(db_session, job.id, "failed")
        stats = _stats(db_session)
        assert stats["total_runs"] == 3
        assert stats["success"] == 2
        assert stats["failed"] == 1
        assert stats["success_rate"] == 2 / 3 * 100

    def test_only_active_jobs_counted(self, db_session):
        _make_job(db_session, name="a", is_active=True)
        _make_job(db_session, name="b", is_active=False)
        stats = _stats(db_session)
        assert stats["total_jobs"] == 2
        assert stats["active_jobs"] == 1


class TestPages:
    def test_dashboard_renders(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "Dashboard" in resp.text or "dashboard" in resp.text.lower()

    def test_jobs_page_renders(self, client):
        resp = client.get("/jobs")
        assert resp.status_code == 200

    def test_runs_page_renders(self, client):
        resp = client.get("/runs")
        assert resp.status_code == 200

    def test_new_job_form(self, client):
        resp = client.get("/jobs/new")
        assert resp.status_code == 200

    def test_run_detail_404_when_missing(self, client):
        assert client.get("/runs/999").status_code == 404


class TestLogPolling:
    """Regression: endpoint must respond 286 when run finished so htmx stops polling."""

    def test_running_returns_200(self, client, db_session):
        job = _make_job(db_session)
        run = _make_run(db_session, job.id, "running")
        resp = client.get(f"/runs/{run.id}/log")
        assert resp.status_code == 200

    def test_finished_returns_286(self, client, db_session):
        job = _make_job(db_session)
        run = _make_run(db_session, job.id, "success")
        resp = client.get(f"/runs/{run.id}/log")
        assert resp.status_code == 286

    def test_failed_returns_286(self, client, db_session):
        job = _make_job(db_session)
        run = _make_run(db_session, job.id, "failed")
        resp = client.get(f"/runs/{run.id}/log")
        assert resp.status_code == 286
