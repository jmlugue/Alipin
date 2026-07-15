"""Editable app configuration for the Alipin V1 prototype."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "apps.json"


class ConfigError(ValueError):
    """Raised when the editable app config is invalid."""


@dataclass(frozen=True)
class LaunchSpec:
    type: str
    command: str | None = None
    uri: str | None = None
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class AppConfig:
    id: str
    display_name: str
    aliases: tuple[str, ...]
    launch: tuple[LaunchSpec, ...]


@dataclass(frozen=True)
class AlipinConfig:
    apps: dict[str, AppConfig]

    def alias_map(self) -> dict[str, AppConfig]:
        aliases: dict[str, AppConfig] = {}
        for app in self.apps.values():
            aliases[normalize_alias(app.id.replace("_", " "))] = app
            aliases[normalize_alias(app.display_name)] = app
            for alias in app.aliases:
                aliases[normalize_alias(alias)] = app
        return aliases


def normalize_alias(value: str) -> str:
    return " ".join(value.lower().strip().split())


def load_config(path: Path | str = DEFAULT_CONFIG_PATH) -> AlipinConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        raw = json.load(file)

    if not isinstance(raw, dict) or not isinstance(raw.get("apps"), dict):
        raise ConfigError("Config must contain an 'apps' object.")

    apps: dict[str, AppConfig] = {}
    for app_id, app_raw in raw["apps"].items():
        apps[app_id] = _parse_app(app_id, app_raw)
    return AlipinConfig(apps=apps)


def _parse_app(app_id: str, raw: Any) -> AppConfig:
    if not isinstance(raw, dict):
        raise ConfigError(f"App '{app_id}' must be an object.")

    display_name = raw.get("display_name")
    aliases = raw.get("aliases")
    launch = raw.get("launch")
    if not isinstance(display_name, str) or not display_name.strip():
        raise ConfigError(f"App '{app_id}' needs a display_name.")
    if not isinstance(aliases, list) or not all(isinstance(item, str) for item in aliases):
        raise ConfigError(f"App '{app_id}' aliases must be a list of strings.")
    if not isinstance(launch, list) or not launch:
        raise ConfigError(f"App '{app_id}' needs at least one launch spec.")

    return AppConfig(
        id=app_id,
        display_name=display_name,
        aliases=tuple(aliases),
        launch=tuple(_parse_launch(app_id, item) for item in launch),
    )


def _parse_launch(app_id: str, raw: Any) -> LaunchSpec:
    if not isinstance(raw, dict):
        raise ConfigError(f"Launch spec for '{app_id}' must be an object.")

    spec_type = raw.get("type")
    if spec_type == "executable":
        command = raw.get("command")
        args = raw.get("args", [])
        if not isinstance(command, str) or not command.strip():
            raise ConfigError(f"Executable launch for '{app_id}' needs command.")
        if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
            raise ConfigError(f"Executable launch args for '{app_id}' must be strings.")
        return LaunchSpec(type=spec_type, command=command, args=tuple(args))

    if spec_type == "uri":
        uri = raw.get("uri")
        if not isinstance(uri, str) or not uri.strip():
            raise ConfigError(f"URI launch for '{app_id}' needs uri.")
        return LaunchSpec(type=spec_type, uri=uri)

    raise ConfigError(f"Unsupported launch type for '{app_id}': {spec_type}")
