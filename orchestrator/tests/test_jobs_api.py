from orchestrator.app.models import Job


def _create(client, **overrides):
    data = {
        "name": "daily build",
        "command": "build",
        "selector": "",
        "cron": "0 2 * * *",
        "is_active": "on",
    }
    data.update(overrides)
    return client.post("/jobs", data=data, follow_redirects=False)


class TestCreateJob:
    def test_happy_path_redirects(self, client, db_session):
        resp = _create(client)
        assert resp.status_code == 303
        assert resp.headers["location"] == "/jobs"
        assert db_session.query(Job).count() == 1

    def test_invalid_command_returns_400(self, client):
        resp = _create(client, command="drop")
        assert resp.status_code == 400
        assert b"Comando" in resp.content

    def test_invalid_cron_returns_400(self, client):
        resp = _create(client, cron="bogus")
        assert resp.status_code == 400

    def test_duplicate_name_rejected(self, client):
        _create(client)
        resp = _create(client)
        assert resp.status_code == 400
        assert "Já existe" in resp.content.decode()


class TestUpdateJob:
    def test_update_persists(self, client, db_session):
        _create(client)
        job = db_session.query(Job).first()
        resp = client.post(
            f"/jobs/{job.id}/update",
            data={"name": "renamed", "command": "test", "selector": "",
                  "cron": "*/5 * * * *", "is_active": "on"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        db_session.refresh(job)
        assert job.name == "renamed"
        assert job.command == "test"

    def test_update_missing_returns_404(self, client):
        resp = client.post(
            "/jobs/999/update",
            data={"name": "x", "command": "build", "selector": "", "cron": "* * * * *"},
        )
        assert resp.status_code == 404


class TestToggleAndDelete:
    def test_toggle_flips_is_active(self, client, db_session):
        _create(client)
        job = db_session.query(Job).first()
        assert job.is_active is True
        client.post(f"/jobs/{job.id}/toggle", follow_redirects=False)
        db_session.refresh(job)
        assert job.is_active is False

    def test_delete_removes_row(self, client, db_session):
        _create(client)
        job_id = db_session.query(Job).first().id
        resp = client.post(f"/jobs/{job_id}/delete", follow_redirects=False)
        assert resp.status_code == 303
        assert db_session.query(Job).count() == 0


class TestRunNow:
    def test_creates_run_and_redirects(self, client, db_session, fake_trigger_run):
        _create(client)
        job_id = db_session.query(Job).first().id
        resp = client.post(f"/jobs/{job_id}/run", follow_redirects=False)
        assert resp.status_code == 303
        assert resp.headers["location"].startswith("/runs/")
        assert len(fake_trigger_run) == 1
        assert fake_trigger_run[0] == (job_id, "manual")
