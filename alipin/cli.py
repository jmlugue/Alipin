"""Command-line entrypoint for the text-first Alipin prototype."""

from __future__ import annotations

import argparse
from pathlib import Path

from alipin.apps import launch_app
from alipin.config import AssistantConfig
from alipin.notes import save_note
from alipin.router import route_command


def handle_command(command: str, config: AssistantConfig) -> str:
    """Route and execute one text command."""
    intent = route_command(command)

    if intent.name == "note":
        note_path = save_note(intent.payload, config.notes_dir)
        return f"Saved note: {note_path}"
    if intent.name == "app":
        return launch_app(intent.payload, config).message
    if intent.name == "web_search":
        return f"Web search is planned next. Search query: {intent.payload}"
    if intent.name == "qa":
        return f"Question answering is planned next. Question: {intent.payload}"
    return f"Conversation fallback: {intent.payload}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Try the text-first Alipin assistant prototype.")
    parser.add_argument("command", nargs="*", help="Command text, for example: take a note buy milk")
    parser.add_argument("--notes-dir", default="notes", help="Directory for saved Markdown notes.")
    parser.add_argument("--launch-apps", action="store_true", help="Actually launch allowlisted apps instead of dry-running.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    command = " ".join(args.command).strip()
    if not command:
        command = input("Alipin command> ").strip()

    config = AssistantConfig(notes_dir=Path(args.notes_dir), dry_run_apps=not args.launch_apps)
    print(handle_command(command, config))


if __name__ == "__main__":
    main()
