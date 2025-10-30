from __future__ import annotations

import argparse
import threading
import time

import requests
import uvicorn
import webview

BACKEND_MODULE = "backend.main:app"


def _run_backend(host: str, port: int) -> None:
    uvicorn.run(BACKEND_MODULE, host=host, port=port, reload=False, log_level="info")


def _wait_for_backend(url: str, timeout: float = 15.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(url, timeout=1)
            if response.ok:
                return
        except requests.RequestException:
            time.sleep(0.2)
    raise RuntimeError(f"Backend did not start at {url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the BONELAB Mod Manager desktop shell")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface for the embedded server")
    parser.add_argument("--port", type=int, default=8777, help="Port for the embedded server")
    args = parser.parse_args()

    backend_thread = threading.Thread(target=_run_backend, args=(args.host, args.port), daemon=True)
    backend_thread.start()

    _wait_for_backend(f"http://{args.host}:{args.port}/app/")

    webview.create_window("BONELAB Mod Manager", f"http://{args.host}:{args.port}/app/")
    webview.start()


if __name__ == "__main__":
    main()
