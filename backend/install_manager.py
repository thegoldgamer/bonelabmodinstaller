from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

import requests

from .state_manager import InstalledFile, InstalledMod, StateManager
from .thunderstore import (
    ThunderstoreError,
    get_package,
    latest_version,
)

MELON_LOADER_PREFIX = "LavaGang-MelonLoader"


class InstallError(RuntimeError):
    pass


class InstallManager:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    @property
    def game_directory(self) -> Optional[Path]:
        game_dir = self.state_manager.state.game_directory
        return Path(game_dir) if game_dir else None

    def ensure_game_directory(self) -> Path:
        game_dir = self.game_directory
        if game_dir is None:
            raise InstallError("Game directory not configured")
        if not game_dir.exists():
            raise InstallError("Configured game directory does not exist")
        (game_dir / "Mods").mkdir(exist_ok=True)
        (game_dir / "Plugins").mkdir(exist_ok=True)
        return game_dir

    def install(self, namespace: str, name: str, version: Optional[str] = None) -> InstalledMod:
        if self.state_manager.is_blacklisted(namespace, name):
            raise InstallError("Mod is blacklisted. Whitelist it to install.")

        package = get_package(namespace, name)
        version_info = self._select_version(package, version)

        dependencies = [
            dep
            for dep in version_info.get("dependencies", [])
            if not dep.startswith(MELON_LOADER_PREFIX)
        ]

        installed_dependencies: List[InstalledMod] = []
        for dep in dependencies:
            dep_namespace, dep_name, *_ = dep.split("-")
            if self.state_manager.get_installed_mod(dep_namespace, dep_name):
                continue
            installed_dependencies.append(self.install(dep_namespace, dep_name))

        download_url = version_info["download_url"]
        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = Path(tmpdir) / "package.zip"
            self._download_file(download_url, archive_path)
            extracted_dir = Path(tmpdir) / "extracted"
            extracted_dir.mkdir()
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(extracted_dir)

            installed_files = self._copy_mod_files(extracted_dir)

        mod = InstalledMod(
            namespace=namespace,
            name=name,
            version=version_info["version_number"],
            display_name=package.get("name", name),
            author=package.get("owner", "Unknown"),
            summary=package.get("description", ""),
            download_url=download_url,
            icon=package.get("icon"),
            dependencies=dependencies,
            installed_files=[InstalledFile(relative_path=f) for f in installed_files],
        )
        self.state_manager.install_mod(mod)
        return mod

    def uninstall(self, namespace: str, name: str) -> None:
        mod = self.state_manager.uninstall_mod(namespace, name)
        if not mod:
            return
        game_dir = self.game_directory
        if game_dir is None:
            return
        for installed_file in mod.installed_files:
            target = game_dir / installed_file.relative_path
            if target.exists():
                target.unlink()

    def _select_version(self, package: Dict, version: Optional[str]) -> Dict:
        if version:
            for candidate in package.get("versions", []):
                if candidate.get("version_number") == version:
                    return candidate
            raise InstallError("Requested version not found")
        return latest_version(package)

    def _download_file(self, url: str, destination: Path) -> None:
        response = requests.get(url, stream=True)
        if response.status_code != 200:
            raise InstallError(f"Failed to download package: {response.status_code}")
        with destination.open("wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    def _copy_mod_files(self, extracted_dir: Path) -> List[str]:
        game_dir = self.ensure_game_directory()
        mods_folder = game_dir / "Mods"
        plugins_folder = game_dir / "Plugins"

        installed_files: List[str] = []

        def copy_contents(source_dir: Path, target_dir: Path) -> None:
            for item in source_dir.iterdir():
                target = target_dir / item.name
                if item.is_dir():
                    target.mkdir(exist_ok=True)
                    copy_contents(item, target)
                else:
                    shutil.copy2(item, target)
                    relative = target.relative_to(game_dir)
                    installed_files.append(str(relative))

        candidate_dirs: List[Path] = []
        for directory in extracted_dir.rglob("*"):
            if directory.is_dir() and directory.name.lower() in {"mods", "plugins"}:
                candidate_dirs.append(directory)

        if extracted_dir.is_dir() and extracted_dir.name.lower() in {"mods", "plugins"}:
            candidate_dirs.append(extracted_dir)

        for directory in candidate_dirs:
            lower_name = directory.name.lower()
            target_dir = mods_folder if lower_name == "mods" else plugins_folder
            copy_contents(directory, target_dir)
        if not installed_files:
            # If no explicit mods/plugins directories were found, copy everything into Mods.
            copy_contents(extracted_dir, mods_folder)
        return installed_files
