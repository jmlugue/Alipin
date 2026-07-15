"""Compatibility router for the command-only Alipin V1 prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from alipin.commands import CommandKind, UNSUPPORTED_MESSAGE, parse_command
from alipin.config import AlipinConfig, load_config

IntentName = Literal["open_app", "spotify_search", "media", "unsupported"]


@dataclass(frozen=True)
class Intent:
    """A routed command-only intent."""

    name: IntentName
    payload: str
    reason: str


def route_command(command: str, config: AlipinConfig | None = None) -> Intent:
    """Route text to allowlisted local desktop commands only."""
    parsed = parse_command(command, config or load_config())
    if parsed.kind is CommandKind.UNSUPPORTED:
        return Intent("unsupported", parsed.message, UNSUPPORTED_MESSAGE)
    payload = parsed.song or parsed.media_action or (parsed.app.id if parsed.app else "")
    return Intent(parsed.kind.value, payload, parsed.action_label)
