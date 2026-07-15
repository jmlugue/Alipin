from alipin.commands import CommandKind, UNSUPPORTED_MESSAGE, parse_command
from alipin.config import load_config
from alipin.router import route_command


CONFIG = load_config()


def test_parses_app_aliases():
    cases = {
        "open Chrome": "chrome",
        "hey Alipin open Edge": "edge",
        "launch File Explorer": "file_explorer",
        "open Notepad": "notepad",
        "open VS Code": "vscode",
        "open Spotify": "spotify",
        "open Settings": "settings",
    }
    for text, app_id in cases.items():
        command = parse_command(text, CONFIG)
        assert command.kind is CommandKind.OPEN_APP
        assert command.app is not None
        assert command.app.id == app_id


def test_parses_media_controls():
    cases = {
        "play music": "play_pause",
        "pause music": "play_pause",
        "next song": "next",
        "previous song": "previous",
    }
    for text, action in cases.items():
        command = parse_command(text, CONFIG)
        assert command.kind is CommandKind.MEDIA
        assert command.media_action == action


def test_parses_spotify_song_search():
    command = parse_command("play Blinding Lights", CONFIG)

    assert command.kind is CommandKind.SPOTIFY_SEARCH
    assert command.song == "blinding lights"


def test_rejects_ai_and_web_prompts():
    cases = [
        "what is the weather?",
        "search the web for Python tutorials",
        "tell me a joke",
        "summarize this article",
        "open youtube dot com",
        "take a note buy oat milk",
    ]
    for text in cases:
        command = parse_command(text, CONFIG)
        assert command.kind is CommandKind.UNSUPPORTED
        assert command.message == UNSUPPORTED_MESSAGE


def test_compatibility_router_fails_closed_for_questions():
    intent = route_command("what is the weather?", CONFIG)

    assert intent.name == "unsupported"
    assert intent.reason == UNSUPPORTED_MESSAGE
