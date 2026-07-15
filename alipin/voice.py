from __future__ import annotations

import json
import os
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path


class VoiceUnavailable(RuntimeError):
    """Raised when local speech recognition cannot be used."""


@dataclass(frozen=True)
class VoiceResult:
    text: str
    engine: str


class VoiceListener:
    def __init__(self, model_path: str | os.PathLike[str] | None = None, sample_rate: int = 16000) -> None:
        self.model_path = Path(model_path or os.environ.get("ALIPIN_VOSK_MODEL", ""))
        self.sample_rate = sample_rate
        self.stop_event = threading.Event()

    def available(self) -> tuple[bool, str]:
        try:
            import sounddevice  # noqa: F401
            import vosk  # noqa: F401
        except ImportError as exc:
            return False, f"Voice dependencies are not installed: {exc.name}"

        if not str(self.model_path) or not self.model_path.exists():
            return False, "Set ALIPIN_VOSK_MODEL to a local Vosk model folder."
        return True, "Vosk ready."

    def stop(self) -> None:
        self.stop_event.set()

    def listen_once(self, timeout_seconds: float = 7.0) -> VoiceResult:
        ready, reason = self.available()
        if not ready:
            raise VoiceUnavailable(reason)

        import sounddevice as sd
        import vosk

        self.stop_event.clear()
        audio: queue.Queue[bytes] = queue.Queue()
        model = vosk.Model(str(self.model_path))
        recognizer = vosk.KaldiRecognizer(model, self.sample_rate)

        def callback(indata: bytes, frames: int, time_info: object, status: object) -> None:
            del frames, time_info
            if status:
                return
            audio.put(bytes(indata))

        deadline = time.monotonic() + timeout_seconds
        with sd.RawInputStream(
            samplerate=self.sample_rate,
            blocksize=8000,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while not self.stop_event.is_set() and time.monotonic() < deadline:
                try:
                    chunk = audio.get(timeout=0.2)
                except queue.Empty:
                    continue
                if recognizer.AcceptWaveform(chunk):
                    text = _extract_text(recognizer.Result())
                    if text:
                        return VoiceResult(text=text, engine="vosk")

        text = _extract_text(recognizer.FinalResult())
        if not text:
            raise VoiceUnavailable("No speech was recognized.")
        return VoiceResult(text=text, engine="vosk")


def _extract_text(raw_json: str) -> str:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError:
        return ""
    text = payload.get("text", "")
    return text if isinstance(text, str) else ""
