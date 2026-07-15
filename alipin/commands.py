from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from alipin.config import AlipinConfig, AppConfig, normalize_alias


UNSUPPORTED_MESSAGE = "That command is not supported yet."


class CommandKind(str, Enum):
    OPEN_APP = "open_app"
    SPOTIFY_SEARCH = "spotify_search"
    MEDIA = "media"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class ParsedCommand:
    kind: CommandKind
    heard_text: str
    action_label: str
    app: AppConfig | None = None
    media_action: str | None = None
    song: str | None = None
    message: str = ""

    @property
    def is_supported(self) -> bool:
        return self.kind is not CommandKind.UNSUPPORTED


_WAKE_PREFIX = re.compile(r"^(?:hey\s+)?alipin[\s,.:;-]+", re.IGNORECASE)
_PLEASE_PREFIX = re.compile(r"^(?:please\s+|can you\s+|could you\s+)", re.IGNORECASE)
_QUESTION_OR_WEB_INTENT = re.compile(
    r"\b("
    r"what|who|when|where|why|how|weather|forecast|search|google|bing|browse|"
    r"website|web|internet|summarize|explain|tell me|advise|advice"
    r")\b",
    re.IGNORECASE,
)
_OPEN_PREFIXES = ("open ", "launch ", "start ")


def parse_command(text: str, config: AlipinConfig) -> ParsedCommand:
    heard = " ".join(text.strip().split())
    normalized = _normalize_command_text(heard)
    if not normalized:
        return _unsupported(heard)

    media = _parse_media(normalized, heard)
    if media:
        return media

    app = _parse_open_app(normalized, heard, config)
    if app:
        return app

    song = _parse_song_search(normalized)
    if song:
        return ParsedCommand(
            kind=CommandKind.SPOTIFY_SEARCH,
            heard_text=heard,
            action_label=f"Open Spotify search: {song}",
            song=song,
        )

    return _unsupported(heard)


def _normalize_command_text(text: str) -> str:
    value = text.lower().strip()
    value = _WAKE_PREFIX.sub("", value)
    value = _PLEASE_PREFIX.sub("", value)
    value = value.rstrip(".!?")
    return " ".join(value.split())


def _parse_media(normalized: str, heard: str) -> ParsedCommand | None:
    media_aliases = {
        "play music": ("play_pause", "Media play/pause"),
        "pause music": ("play_pause", "Media play/pause"),
        "pause": ("play_pause", "Media play/pause"),
        "resume music": ("play_pause", "Media play/pause"),
        "next song": ("next", "Media next"),
        "next track": ("next", "Media next"),
        "skip song": ("next", "Media next"),
        "previous song": ("previous", "Media previous"),
        "previous track": ("previous", "Media previous"),
        "last song": ("previous", "Media previous"),
    }
    match = media_aliases.get(normalized)
    if not match:
        return None
    media_action, label = match
    return ParsedCommand(
        kind=CommandKind.MEDIA,
        heard_text=heard,
        action_label=label,
        media_action=media_action,
    )


def _parse_open_app(normalized: str, heard: str, config: AlipinConfig) -> ParsedCommand | None:
    target = None
    for prefix in _OPEN_PREFIXES:
        if normalized.startswith(prefix):
            target = normalized.removeprefix(prefix).strip()
            break
    if not target:
        return None

    app = config.alias_map().get(normalize_alias(target))
    if not app:
        return None

    return ParsedCommand(
        kind=CommandKind.OPEN_APP,
        heard_text=heard,
        action_label=f"Open {app.display_name}",
        app=app,
    )


def _parse_song_search(normalized: str) -> str | None:
    if not normalized.startswith("play "):
        return None

    song = normalized.removeprefix("play ").strip()
    if not song or song in {"music", "song", "track"}:
        return None
    if _QUESTION_OR_WEB_INTENT.search(song):
        return None
    return song


def _unsupported(heard: str) -> ParsedCommand:
    return ParsedCommand(
        kind=CommandKind.UNSUPPORTED,
        heard_text=heard,
        action_label="Unsupported",
        message=UNSUPPORTED_MESSAGE,
    )
