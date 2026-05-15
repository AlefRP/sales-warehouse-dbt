from orchestrator.app.routes.jobs import VALID_COMMANDS, _validate


class TestValidate:
    def test_valid_input_returns_none(self):
        assert _validate("daily build", "build", "0 2 * * *") is None

    def test_empty_name_rejected(self):
        assert "Nome" in _validate("", "build", "0 2 * * *")

    def test_too_long_name_rejected(self):
        assert "Nome" in _validate("x" * 101, "build", "0 2 * * *")

    def test_invalid_command_rejected(self):
        msg = _validate("ok", "drop-table", "0 2 * * *")
        assert msg is not None
        assert "Comando" in msg

    def test_invalid_cron_rejected(self):
        msg = _validate("ok", "build", "not a cron")
        assert msg is not None
        assert "cron" in msg.lower()

    def test_all_valid_commands_pass(self):
        for cmd in VALID_COMMANDS:
            assert _validate("name", cmd, "* * * * *") is None, cmd
