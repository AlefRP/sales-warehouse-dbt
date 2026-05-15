from datetime import datetime

from orchestrator.app.main import _fmt_dt, _fmt_duration


class TestFmtDt:
    def test_none_is_em_dash(self):
        assert _fmt_dt(None) == "—"

    def test_datetime_formatted(self):
        assert _fmt_dt(datetime(2026, 1, 2, 3, 4, 5)) == "2026-01-02 03:04:05"

    def test_string_passthrough(self):
        assert _fmt_dt("anything") == "anything"


class TestFmtDuration:
    def test_none(self):
        assert _fmt_duration(None) == "—"

    def test_seconds(self):
        assert _fmt_duration(42) == "42s"

    def test_minutes(self):
        assert _fmt_duration(125) == "2m05s"

    def test_hours(self):
        assert _fmt_duration(3725) == "1h02m05s"

    def test_zero(self):
        assert _fmt_duration(0) == "0s"
