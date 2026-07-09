"""Deterministic intent router for the first Alipin prototype."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

IntentName = Literal["note", "app", "web_search", "qa", "conversation"]


@dataclass(frozen=True)
class Intent:
    """A routed assistant intent."""

    name: IntentName
    payload: str
    reason: str


NOTE_PREFIXES = ("take a note", "write this down", "remember this", "note")
APP_PREFIXES = ("open", "launch", "start")
WEB_PREFIXES = ("search for", "look up", "web search")
QA_PREFIXES = ("what is", "who is", "when is", "where is", "why is", "how do", "how does")


def _strip_prefix(command: str, prefixes: tuple[str, ...]) -> str:
    lowered = command.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return command[len(prefix) :].strip(" :,-")
    return command.strip()


def route_command(command: str) -> Intent:
    """Route text to a small set of auditable assistant skills."""
    cleaned = command.strip()
    lowered = cleaned.lower()
    if not cleaned:
        return Intent("conversation", "", "No command text was provided.")

    if lowered.startswith(NOTE_PREFIXES):
        return Intent("note", _strip_prefix(cleaned, NOTE_PREFIXES), "Matched a note-taking phrase.")
    if lowered.startswith(APP_PREFIXES):
        return Intent("app", _strip_prefix(cleaned, APP_PREFIXES), "Matched an app-launch phrase.")
    if lowered.startswith(WEB_PREFIXES):
        return Intent("web_search", _strip_prefix(cleaned, WEB_PREFIXES), "Matched a web-search phrase.")
    if lowered.startswith(QA_PREFIXES) or lowered.endswith("?"):
        return Intent("qa", cleaned, "Matched a question phrase or question mark.")

    return Intent("conversation", cleaned, "No specific skill matched; using conversation fallback.")
