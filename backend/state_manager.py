from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

STATE_FILE = Path(__file__).resolve().parent / "data" / "state.json"


@dataclass
class InstalledFile:
    relative_path: str


@dataclass
class InstalledMod:
    namespace: str
    name: str
    version: str
    display_name: str
    author: str
    summary: str
    download_url: str
    icon: Optional[str]
    dependencies: List[str] = field(default_factory=list)
    installed_files: List[InstalledFile] = field(default_factory=list)

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["installed_files"] = [asdict(f) for f in self.installed_files]
        return data

    @staticmethod
    def from_dict(data: Dict) -> "InstalledMod":
        files = [InstalledFile(**f) for f in data.get("installed_files", [])]
        return InstalledMod(
            namespace=data["namespace"],
            name=data["name"],
            version=data["version"],
            display_name=data.get("display_name", data["name"]),
            author=data.get("author", "Unknown"),
            summary=data.get("summary", ""),
            download_url=data.get("download_url", ""),
            icon=data.get("icon"),
            dependencies=data.get("dependencies", []),
            installed_files=files,
        )


@dataclass
class AppState:
    game_directory: Optional[str] = None
    installed_mods: Dict[str, InstalledMod] = field(default_factory=dict)
    blacklisted_mods: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "game_directory": self.game_directory,
            "installed_mods": {k: v.to_dict() for k, v in self.installed_mods.items()},
            "blacklisted_mods": self.blacklisted_mods,
        }

    @staticmethod
    def from_dict(data: Dict) -> "AppState":
        installed = {
            key: InstalledMod.from_dict(value)
            for key, value in data.get("installed_mods", {}).items()
        }
        return AppState(
            game_directory=data.get("game_directory"),
            installed_mods=installed,
            blacklisted_mods=data.get("blacklisted_mods", []),
        )


class StateManager:
    def __init__(self, state_file: Path = STATE_FILE):
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    def _load_state(self) -> AppState:
        if not self.state_file.exists():
            return AppState()
        with self.state_file.open("r", encoding="utf-8") as f:
            raw = json.load(f)
        return AppState.from_dict(raw)

    def save(self) -> None:
        with self.state_file.open("w", encoding="utf-8") as f:
            json.dump(self._state.to_dict(), f, indent=2)

    @property
    def state(self) -> AppState:
        return self._state

    def update_game_directory(self, path: str) -> None:
        self._state.game_directory = path
        self.save()

    def install_mod(self, mod: InstalledMod) -> None:
        key = f"{mod.namespace}.{mod.name}"
        self._state.installed_mods[key] = mod
        self.save()

    def uninstall_mod(self, namespace: str, name: str) -> Optional[InstalledMod]:
        key = f"{namespace}.{name}"
        mod = self._state.installed_mods.pop(key, None)
        if mod:
            self.save()
        return mod

    def get_installed_mod(self, namespace: str, name: str) -> Optional[InstalledMod]:
        key = f"{namespace}.{name}"
        return self._state.installed_mods.get(key)

    def list_installed_mods(self) -> List[InstalledMod]:
        return list(self._state.installed_mods.values())

    def add_to_blacklist(self, namespace: str, name: str) -> None:
        key = f"{namespace}.{name}"
        if key not in self._state.blacklisted_mods:
            self._state.blacklisted_mods.append(key)
            self.save()

    def remove_from_blacklist(self, namespace: str, name: str) -> None:
        key = f"{namespace}.{name}"
        if key in self._state.blacklisted_mods:
            self._state.blacklisted_mods.remove(key)
            self.save()

    def is_blacklisted(self, namespace: str, name: str) -> bool:
        key = f"{namespace}.{name}"
        return key in self._state.blacklisted_mods

    def list_blacklisted_mods(self) -> List[str]:
        return list(self._state.blacklisted_mods)
