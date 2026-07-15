from alipin.actions import ActionExecutor
from alipin.commands import CommandKind, parse_command
from alipin.config import load_config


CONFIG = load_config()
EXECUTOR = ActionExecutor(dry_run=True)


def test_open_app_dry_run():
    command = parse_command("open Notepad", CONFIG)
    outcome = EXECUTOR.execute(command)

    assert outcome.ok is True
    assert "notepad.exe" in outcome.detail


def test_spotify_search_dry_run():
    command = parse_command("play Blinding Lights", CONFIG)
    outcome = EXECUTOR.execute(command)

    assert outcome.ok is True
    assert outcome.detail == "spotify:search:blinding%20lights"


def test_media_dry_run():
    command = parse_command("next song", CONFIG)
    outcome = EXECUTOR.execute(command)

    assert outcome.ok is True


def test_unsupported_does_not_dispatch():
    command = parse_command("what is the weather?", CONFIG)
    outcome = EXECUTOR.execute(command)

    assert command.kind is CommandKind.UNSUPPORTED
    assert outcome.ok is False
    assert outcome.message == "That command is not supported yet."
