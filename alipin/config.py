"""Configuration defaults for the Alipin prototype."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys


def _discord_command() -> tuple[str, ...]:
    if sys.platform == "win32":
        return ("cmd", "/c", "start", "", "discord:")
    if sys.platform == "darwin":
        return ("open", "-a", "Discord")
    return ("discord",)


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
    notes_dir: Path = Path("D:/AI Notes")
    dry_run_apps: bool = True
    hf_model: str = "openai/gpt-oss-120b:together"
    hf_token_env: str = "HUGGINGFACE_API_TOKEN"
    enable_web_search: bool = True
    search_provider: str = "searxng"
    searxng_url: str | None = None
    serpapi_key_env: str = "SERPAPI_API_KEY"
    apps: tuple[AppCommand, ...] = (
        AppCommand("discord", _discord_command(), ("disc", "discord app")),
    )
