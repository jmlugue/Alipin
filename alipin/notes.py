"""Local text note-taking skill."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40] or "note"


def save_note(content: str, notes_dir: Path) -> Path:
    """Save a timestamped text note and return its path."""
    cleaned = content.strip()
    if not cleaned:
        raise ValueError("Cannot save an empty note.")

    notes_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = notes_dir / f"{timestamp}-{_slugify(cleaned)}.txt"
    path.write_text(f"Note {timestamp} UTC\n\n{cleaned}\n", encoding="utf-8")
    return path
