from pathlib import Path

import pytest

from alipin.notes import save_note


def test_save_note_writes_text_file(tmp_path: Path):
    note = save_note("Remember the prototype", tmp_path)

    assert note.exists()
    assert note.suffix == ".txt"
    assert "Remember the prototype" in note.read_text(encoding="utf-8")


def test_save_note_rejects_empty_note(tmp_path: Path):
    with pytest.raises(ValueError):
        save_note("   ", tmp_path)
