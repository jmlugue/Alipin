from __future__ import annotations

import threading
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from alipin.actions import ActionExecutor
from alipin.commands import parse_command
from alipin.config import ConfigError, load_config
from alipin.voice import VoiceListener, VoiceUnavailable


class AlipinWindow:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Alipin")
        self.root.geometry("560x360")
        self.root.minsize(460, 320)

        self.config = load_config()
        self.executor = ActionExecutor()
        self.voice = VoiceListener()

        self.status = tk.StringVar(value=self._voice_status())
        self.heard_text = tk.StringVar(value="")
        self.action_text = tk.StringVar(value="")
        self.result_text = tk.StringVar(value="")
        self.test_command = tk.StringVar(value="open Spotify")

        self._build()

    def _build(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        frame = ttk.Frame(self.root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Alipin", font=("Segoe UI", 20, "bold")).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(0, 12),
        )
        self._row(frame, 1, "Status", self.status)
        self._row(frame, 2, "Heard", self.heard_text)
        self._row(frame, 3, "Action", self.action_text)
        self._row(frame, 4, "Result", self.result_text)

        ttk.Label(frame, text="Test").grid(row=5, column=0, sticky="w", pady=(18, 4))
        test_entry = ttk.Entry(frame, textvariable=self.test_command)
        test_entry.grid(row=5, column=1, columnspan=2, sticky="ew", pady=(18, 4))
        test_entry.bind("<Return>", lambda _event: self.run_text(self.test_command.get()))

        controls = ttk.Frame(frame)
        controls.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        controls.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(controls, text="Listen", command=self.listen).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        ttk.Button(controls, text="Stop", command=self.stop).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(controls, text="Test Command", command=lambda: self.run_text(self.test_command.get())).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(8, 0),
        )

    def _row(self, parent: ttk.Frame, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="nw", pady=5)
        ttk.Label(parent, textvariable=variable, wraplength=390, justify="left").grid(
            row=row,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=5,
        )

    def _voice_status(self) -> str:
        ready, reason = self.voice.available()
        return reason if ready else f"Typed fallback ready. {reason}"

    def listen(self) -> None:
        self.status.set("Listening...")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self) -> None:
        try:
            result = self.voice.listen_once()
            self.root.after(0, lambda: self.run_text(result.text))
        except VoiceUnavailable:
            self.root.after(0, self._typed_fallback)
        except Exception as exc:
            self.root.after(0, lambda: self._set_error(f"Voice error: {exc}"))

    def _typed_fallback(self) -> None:
        self.status.set(self._voice_status())
        text = simpledialog.askstring("Alipin", "Command")
        if text:
            self.run_text(text)

    def stop(self) -> None:
        self.voice.stop()
        self.status.set("Stopped.")

    def run_text(self, text: str) -> None:
        command = parse_command(text, self.config)
        self.heard_text.set(command.heard_text)
        self.action_text.set(command.action_label)

        outcome = self.executor.execute(command)
        result = outcome.message if not outcome.detail else f"{outcome.message} ({outcome.detail})"
        self.result_text.set(result)
        self.status.set("Ready." if outcome.ok else "Unsupported.")

    def _set_error(self, message: str) -> None:
        self.status.set("Error.")
        self.result_text.set(message)


def main() -> None:
    root = tk.Tk()
    try:
        AlipinWindow(root)
    except ConfigError as exc:
        messagebox.showerror("Alipin config error", str(exc))
        raise SystemExit(1) from exc
    root.mainloop()
