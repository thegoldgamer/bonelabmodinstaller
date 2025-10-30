from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional

import requests

THUNDERSTORE_BASE = "https://thunderstore.io/api/experimental/package"
REQUEST_TIMEOUT = 30


class ThunderstoreError(RuntimeError):
    pass


def _get(url: str) -> requests.Response:
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
    except requests.RequestException as exc:
        raise ThunderstoreError(f"Thunderstore request failed: {exc}") from exc
    if response.status_code != 200:
        raise ThunderstoreError(
            f"Thunderstore API error ({response.status_code}): {response.text}"
        )
    return response


@lru_cache(maxsize=1)
def fetch_all_packages() -> List[Dict]:
    response = _get(f"{THUNDERSTORE_BASE}/")
    return response.json()


def search_packages(query: Optional[str] = None) -> List[Dict]:
    packages = fetch_all_packages()
    if not query:
        return packages
    lowered = query.lower()
    return [
        package
        for package in packages
        if lowered in package["name"].lower()
        or lowered in package["full_name"].lower()
        or lowered in package["owner"].lower()
        or lowered in package.get("latest", {}).get("description", "").lower()
    ]


def get_package(namespace: str, name: str) -> Dict:
    response = _get(f"{THUNDERSTORE_BASE}/{namespace}/{name}/")
    return response.json()


def latest_version(package: Dict) -> Dict:
    versions = package.get("versions", [])
    if not versions:
        raise ThunderstoreError("Package has no versions")
    return versions[0]


def format_dependency(dep: str) -> str:
    if "-" not in dep:
        return dep
    parts = dep.split("-")
    if len(parts) < 2:
        return dep
    namespace, name = parts[0], parts[1]
    return f"{namespace}.{name}"
