from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .install_manager import InstallError, InstallManager
from .state_manager import InstalledMod, StateManager
from .thunderstore import (
    ThunderstoreError,
    format_dependency,
    get_package,
    search_packages,
)

app = FastAPI(title="BONELAB Mod Manager API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"]
    ,
    allow_headers=["*"],
)

state_manager = StateManager()
install_manager = InstallManager(state_manager)


class ModSummary(BaseModel):
    namespace: str
    name: str
    display_name: str
    summary: str
    owner: str
    icon: Optional[str]
    downloads: int
    latest_version: str


class ModDetail(ModSummary):
    description: str
    dependencies: List[str]
    versions: List[Dict]


class InstallRequest(BaseModel):
    namespace: str
    name: str
    version: Optional[str] = None


class BlacklistRequest(BaseModel):
    namespace: str
    name: str


class GameDirectoryRequest(BaseModel):
    path: str


class InstalledFileModel(BaseModel):
    relative_path: str


class InstalledModModel(BaseModel):
    namespace: str
    name: str
    version: str
    display_name: str
    author: str
    summary: str
    download_url: str
    icon: Optional[str]
    dependencies: List[str]
    installed_files: List[InstalledFileModel]


def map_package_to_summary(package: Dict) -> ModSummary:
    latest = package.get("versions", [{}])[0]
    return ModSummary(
        namespace=package.get("namespace", package.get("owner", "")),
        name=package.get("name", ""),
        display_name=package.get("display_name", package.get("name", "")),
        summary=package.get("description", ""),
        owner=package.get("owner", ""),
        icon=package.get("icon"),
        downloads=latest.get("downloads", 0),
        latest_version=latest.get("version_number", ""),
    )


@app.get("/api/mods", response_model=List[ModSummary])
def list_mods(search: Optional[str] = None, limit: int = 50, offset: int = 0):
    try:
        packages = search_packages(search)
    except ThunderstoreError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    sliced = packages[offset : offset + limit]
    return [map_package_to_summary(pkg) for pkg in sliced]


@app.get("/api/mods/{namespace}/{name}", response_model=ModDetail)
def get_mod_detail(namespace: str, name: str):
    try:
        package = get_package(namespace, name)
    except ThunderstoreError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    latest = package.get("versions", [{}])[0]
    dependencies = [
        dep
        for dep in latest.get("dependencies", [])
        if not dep.startswith("LavaGang-MelonLoader")
    ]
    formatted_dependencies = [format_dependency(dep) for dep in dependencies]

    return ModDetail(
        namespace=package.get("namespace", namespace),
        name=package.get("name", name),
        display_name=package.get("display_name", package.get("name", name)),
        summary=package.get("description", ""),
        owner=package.get("owner", ""),
        icon=package.get("icon"),
        downloads=latest.get("downloads", 0),
        latest_version=latest.get("version_number", ""),
        description=latest.get("description", ""),
        dependencies=formatted_dependencies,
        versions=package.get("versions", []),
    )


@app.post("/api/mods/install", response_model=ModDetail)
def install_mod(request: InstallRequest):
    try:
        mod = install_manager.install(request.namespace, request.name, request.version)
        detail = get_mod_detail(request.namespace, request.name)
        return detail
    except InstallError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/mods/uninstall")
def uninstall_mod(request: InstallRequest):
    install_manager.uninstall(request.namespace, request.name)
    return {"status": "ok"}


@app.post("/api/mods/blacklist")
def blacklist_mod(request: BlacklistRequest):
    state_manager.add_to_blacklist(request.namespace, request.name)
    install_manager.uninstall(request.namespace, request.name)
    return {"status": "ok"}


@app.post("/api/mods/whitelist")
def whitelist_mod(request: BlacklistRequest):
    state_manager.remove_from_blacklist(request.namespace, request.name)
    return {"status": "ok"}


@app.get("/api/mods/installed", response_model=List[InstalledModModel])
def list_installed_mods():
    mods: List[InstalledMod] = state_manager.list_installed_mods()
    return [
        InstalledModModel(
            namespace=mod.namespace,
            name=mod.name,
            version=mod.version,
            display_name=mod.display_name,
            author=mod.author,
            summary=mod.summary,
            download_url=mod.download_url,
            icon=mod.icon,
            dependencies=mod.dependencies,
            installed_files=[
                InstalledFileModel(relative_path=file.relative_path)
                for file in mod.installed_files
            ],
        )
        for mod in mods
    ]


@app.get("/api/mods/blacklisted")
def list_blacklisted_mods():
    return state_manager.list_blacklisted_mods()


@app.post("/api/settings/game-directory")
def set_game_directory(request: GameDirectoryRequest):
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=400, detail="Path does not exist")
    state_manager.update_game_directory(str(path))
    return {"status": "ok"}


@app.get("/api/settings")
def get_settings():
    return {"game_directory": state_manager.state.game_directory}


@app.get("/api/notifications")
def get_notifications():
    notifications = []
    for mod in state_manager.list_installed_mods():
        try:
            package = get_package(mod.namespace, mod.name)
        except ThunderstoreError:
            continue
        latest = package.get("versions", [{}])[0]
        latest_version = latest.get("version_number")
        if latest_version and latest_version != mod.version:
            notifications.append(
                {
                    "namespace": mod.namespace,
                    "name": mod.name,
                    "display_name": mod.display_name,
                    "icon": mod.icon,
                    "current_version": mod.version,
                    "latest_version": latest_version,
                }
            )
    return notifications
