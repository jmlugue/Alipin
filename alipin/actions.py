from __future__ import annotations

import ctypes
import os
import subprocess
from dataclasses import dataclass
from urllib.parse import quote

from alipin.commands import CommandKind, ParsedCommand, UNSUPPORTED_MESSAGE
from alipin.config import LaunchSpec


@dataclass(frozen=True)
class ActionOutcome:
    ok: bool
    message: str
    detail: str = ""


class ActionExecutor:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run

    def execute(self, command: ParsedCommand) -> ActionOutcome:
        if command.kind is CommandKind.UNSUPPORTED:
            return ActionOutcome(ok=False, message=UNSUPPORTED_MESSAGE)
        if command.kind is CommandKind.OPEN_APP and command.app:
            return self._open_app(command)
        if command.kind is CommandKind.SPOTIFY_SEARCH and command.song:
            return self._open_spotify_search(command.song)
        if command.kind is CommandKind.MEDIA and command.media_action:
            return self._send_media_key(command.media_action)
        return ActionOutcome(ok=False, message=UNSUPPORTED_MESSAGE)

    def _open_app(self, command: ParsedCommand) -> ActionOutcome:
        assert command.app is not None
        errors: list[str] = []
        for spec in command.app.launch:
            try:
                detail = self._launch(spec)
                return ActionOutcome(
                    ok=True,
                    message=f"Opened {command.app.display_name}.",
                    detail=detail,
                )
            except OSError as exc:
                errors.append(str(exc))
        return ActionOutcome(
            ok=False,
            message=f"Could not open {command.app.display_name}.",
            detail="; ".join(errors),
        )

    def _launch(self, spec: LaunchSpec) -> str:
        if spec.type == "uri":
            assert spec.uri is not None
            if not self.dry_run:
                os.startfile(spec.uri)  # type: ignore[attr-defined]
            return spec.uri

        if spec.type == "executable":
            assert spec.command is not None
            argv = [spec.command, *spec.args]
            if not self.dry_run:
                subprocess.Popen(argv, close_fds=True)
            return " ".join(argv)

        raise OSError(f"Unsupported launch spec: {spec.type}")

    def _open_spotify_search(self, song: str) -> ActionOutcome:
        uri = f"spotify:search:{quote(song)}"
        if not self.dry_run:
            os.startfile(uri)  # type: ignore[attr-defined]
        return ActionOutcome(ok=True, message=f"Opened Spotify search for {song}.", detail=uri)

    def _send_media_key(self, media_action: str) -> ActionOutcome:
        keys = {
            "play_pause": 0xB3,
            "next": 0xB0,
            "previous": 0xB1,
        }
        key = keys.get(media_action)
        if key is None:
            return ActionOutcome(ok=False, message=UNSUPPORTED_MESSAGE)

        if not self.dry_run:
            user32 = ctypes.windll.user32  # type: ignore[attr-defined]
            user32.keybd_event(key, 0, 0, 0)
            user32.keybd_event(key, 0, 2, 0)

        return ActionOutcome(ok=True, message=f"Sent media command: {media_action}.", detail=str(key))
