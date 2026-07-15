from __future__ import annotations

from difflib import SequenceMatcher
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
    target = _extract_open_target(normalized)
    if not target:
        return None

    app = _match_app(target, config)
    if not app:
        return None

    return ParsedCommand(
        kind=CommandKind.OPEN_APP,
        heard_text=heard,
        action_label=f"Open {app.display_name}",
        app=app,
    )


def _extract_open_target(normalized: str) -> str | None:
    for prefix in _OPEN_PREFIXES:
        if normalized.startswith(prefix):
            return normalized.removeprefix(prefix).strip()

    for marker in (" open ", " launch ", " start "):
        if marker in normalized:
            lead, target = normalized.split(marker, maxsplit=1)
            if _can_ignore_wake_noise(lead):
                return target.strip()
    return None


def _can_ignore_wake_noise(lead: str) -> bool:
    words = lead.split()
    if not words or len(words) > 5:
        return False
    if _QUESTION_OR_WEB_INTENT.search(lead):
        return False
    compact = "".join(words)
    return SequenceMatcher(None, compact, "heyalipin").ratio() >= 0.45


def _match_app(target: str, config: AlipinConfig) -> AppConfig | None:
    aliases = config.alias_map()
    normalized_target = normalize_alias(target)
    exact = aliases.get(normalized_target)
    if exact:
        return exact

    compact_target = normalized_target.replace(" ", "")
    if len(compact_target) < 4:
        return None

    best_app: AppConfig | None = None
    best_score = 0.0
    for alias, app in aliases.items():
        compact_alias = alias.replace(" ", "")
        score = SequenceMatcher(None, compact_target, compact_alias).ratio()
        if score > best_score:
            best_score = score
            best_app = app
    return best_app if best_score >= 0.78 else None


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
