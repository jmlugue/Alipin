"""Command-line helper for exercising Alipin's command-only router."""

from __future__ import annotations

import argparse
import sys

from alipin.actions import ActionExecutor
from alipin.commands import parse_command
from alipin.config import load_config


def handle_command(command: str, *, dry_run: bool = True) -> str:
    """Route and execute one text command."""
    parsed = parse_command(command, load_config())
    outcome = ActionExecutor(dry_run=dry_run).execute(parsed)
    return outcome.message if not outcome.detail else f"{outcome.message} ({outcome.detail})"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Try the command-only Alipin V1 router.")
    parser.add_argument("command", nargs="*", help="Command text, for example: open Spotify")
    parser.add_argument("--launch-apps", action="store_true", help="Actually run allowlisted actions instead of dry-running.")
    return parser


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args()
    command = " ".join(args.command).strip()
    if not command:
        command = input("Alipin command> ").strip()

    print(handle_command(command, dry_run=not args.launch_apps))


if __name__ == "__main__":
    main()
