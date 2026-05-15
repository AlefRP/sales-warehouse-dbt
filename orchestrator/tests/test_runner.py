from orchestrator.app import runner
from orchestrator.app.models import Job


def _job(**kw):
    defaults = dict(id=1, name="t", command="build", selector=None, cron="* * * * *",
                    is_active=True)
    defaults.update(kw)
    return Job(**defaults)


class TestBuildCommand:
    def test_basic_command(self):
        cmd = runner._build_command(_job(command="run"))
        assert cmd[0:2] == ["dbt", "run"]
        assert "--project-dir" in cmd
        assert "--profiles-dir" in cmd
        assert "--target" in cmd

    def test_selector_is_split(self):
        cmd = runner._build_command(_job(command="build", selector="--select tag:staging"))
        assert "--select" in cmd
        assert "tag:staging" in cmd

    def test_no_selector_no_extras(self):
        cmd = runner._build_command(_job(selector=None))
        assert "--select" not in cmd

    def test_quoted_selector_preserved(self):
        cmd = runner._build_command(_job(selector='--select "model with space"'))
        assert "model with space" in cmd
