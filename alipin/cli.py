"""Command-line entrypoint for the text-first Alipin prototype."""

from __future__ import annotations

import argparse
from pathlib import Path

from alipin.apps import launch_app
from alipin.config import AssistantConfig
from alipin.notes import save_note
from alipin.qa import DuckDuckGoSearcher, HuggingFaceTextGenerator, answer_question
from alipin.router import route_command


def handle_command(command: str, config: AssistantConfig) -> str:
    """Route and execute one text command."""
    intent = route_command(command)

    if intent.name == "note":
        note_path = save_note(intent.payload, config.notes_dir)
        return f"Saved note: {note_path}"
    if intent.name == "app":
        return launch_app(intent.payload, config).message
    generator = HuggingFaceTextGenerator(config.hf_model, config.hf_token_env)
    searcher = DuckDuckGoSearcher() if config.enable_web_search else None

    if intent.name == "web_search":
        return answer_question(intent.payload, generator, searcher, force_web=True).answer
    if intent.name == "qa":
        return answer_question(intent.payload, generator, searcher).answer
    return f"Conversation fallback: {intent.payload}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Try the text-first Alipin assistant prototype.")
    parser.add_argument("command", nargs="*", help="Command text, for example: take a note buy milk")
    parser.add_argument("--notes-dir", default="D:/AI Notes", help="Directory for saved text notes.")
    parser.add_argument("--launch-apps", action="store_true", help="Actually launch allowlisted apps instead of dry-running.")
    parser.add_argument("--hf-model", default="HuggingFaceH4/zephyr-7b-beta", help="Hugging Face text-generation model for answers.")
    parser.add_argument("--hf-token-env", default="HUGGINGFACE_API_TOKEN", help="Environment variable that stores the Hugging Face access token.")
    parser.add_argument("--no-web", action="store_true", help="Disable web search context for questions and search commands.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    command = " ".join(args.command).strip()
    if not command:
        command = input("Alipin command> ").strip()

    config = AssistantConfig(
        notes_dir=Path(args.notes_dir),
        dry_run_apps=not args.launch_apps,
        hf_model=args.hf_model,
        hf_token_env=args.hf_token_env,
        enable_web_search=not args.no_web,
    )
    print(handle_command(command, config))


if __name__ == "__main__":
    main()
