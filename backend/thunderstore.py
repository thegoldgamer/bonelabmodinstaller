from __future__ import annotations

from functools import lru_cache
from typing import Dict, List, Optional

import requests

THUNDERSTORE_BASE = "https://thunderstore.io/api/experimental/package"


class ThunderstoreError(RuntimeError):
    pass


def _handle_response(response: requests.Response) -> Dict:
    if response.status_code != 200:
        raise ThunderstoreError(
            f"Thunderstore API error ({response.status_code}): {response.text}"
        )
    return response.json()


@lru_cache(maxsize=1)
def fetch_all_packages() -> List[Dict]:
    response = requests.get(f"{THUNDERSTORE_BASE}/")
    data = _handle_response(response)
    return data


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
    response = requests.get(f"{THUNDERSTORE_BASE}/{namespace}/{name}/")
    return _handle_response(response)


def latest_version(package: Dict) -> Dict:
    versions = package.get("versions", [])
    if not versions:
        raise ThunderstoreError("Package has no versions")
    return versions[0]


def format_dependency(dep: str) -> str:
    return dep.split("-")[0] + "." + dep.split("-")[1] if "-" in dep else dep
