"""Allowlisted app-launching skill."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from alipin.config import AppCommand, AssistantConfig


@dataclass(frozen=True)
class AppLaunchResult:
    """Result of an app-launch request."""

    matched: str | None
    message: str


def _matches(request: str, app: AppCommand) -> bool:
    lowered = request.lower().strip()
    names = (app.name, *app.aliases)
    return any(lowered == name or lowered in name or name in lowered for name in names)


def launch_app(request: str, config: AssistantConfig) -> AppLaunchResult:
    """Launch an allowlisted app, or describe what would happen in dry-run mode."""
    for app in config.apps:
        if _matches(request, app):
            if config.dry_run_apps:
                return AppLaunchResult(app.name, f"Dry run: would launch {app.name} with {app.command!r}.")
            subprocess.Popen(app.command)  # noqa: S603 - command is from a static allowlist.
            return AppLaunchResult(app.name, f"Launching {app.name}.")
    allowed = ", ".join(app.name for app in config.apps)
    return AppLaunchResult(None, f"I can only open allowlisted apps right now: {allowed}.")
