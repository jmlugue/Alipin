"""Configuration defaults for the Alipin prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AppCommand:
    """A safe, allowlisted application command."""

    name: str
    command: tuple[str, ...]
    aliases: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class AssistantConfig:
    """Runtime configuration for the text-first assistant prototype."""

    wake_name: str = "alipin"
    notes_dir: Path = Path("notes")
    dry_run_apps: bool = True
    apps: tuple[AppCommand, ...] = (
        AppCommand("browser", ("xdg-open", "https://www.google.com"), ("web", "internet")),
        AppCommand("notes", ("xdg-open", "notes"), ("note folder", "my notes")),
    )
