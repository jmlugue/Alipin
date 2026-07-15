"""Compatibility wrapper for allowlisted app launching."""

from __future__ import annotations

from dataclasses import dataclass

from alipin.actions import ActionExecutor
from alipin.commands import CommandKind, parse_command
from alipin.config import AlipinConfig, load_config


@dataclass(frozen=True)
class AppLaunchResult:
    """Result of an app-launch request."""

    matched: str | None
    message: str


def launch_app(request: str, config: AlipinConfig | None = None, *, dry_run: bool = True) -> AppLaunchResult:
    """Launch an allowlisted app by name, defaulting to dry-run mode."""
    loaded_config = config or load_config()
    parsed = parse_command(f"open {request}", loaded_config)
    if parsed.kind is not CommandKind.OPEN_APP:
        allowed = ", ".join(app.display_name for app in loaded_config.apps.values())
        return AppLaunchResult(None, f"I can only open allowlisted apps right now: {allowed}.")

    outcome = ActionExecutor(dry_run=dry_run).execute(parsed)
    return AppLaunchResult(parsed.app.id if parsed.app else None, outcome.message)
