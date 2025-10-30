# BONELAB Mod Manager

A desktop-friendly web experience for browsing and managing BONELAB mods with Thunderstore integration. The project contains:

- A FastAPI backend that communicates with the Thunderstore API, installs mods (and their dependencies), handles blacklist/whitelist logic, and keeps track of installed packages.
- A lightweight frontend (vanilla JavaScript + CSS) that mirrors the original UI concept with an animated sidebar, layered mod detail view, and update notifications.

## Getting started

### Requirements

- Python 3.11+
- Node.js (optional – only needed if you plan to use a bundler instead of the provided static frontend)

### Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
pip install fastapi==0.110.0 "uvicorn[standard]==0.27.0" requests==2.31.0 python-multipart==0.0.9
uvicorn backend.main:app --reload
```

The API is now available at `http://localhost:8000`.

### Frontend setup

The frontend is a static site. You can serve it with any HTTP server (Python’s `http.server` works great):

```bash
cd frontend
python -m http.server 5173
```

Open `http://localhost:5173` in your browser. By default the frontend expects the backend at `http://localhost:8000`. To change this, define `API_BASE_URL` before loading the script:

```html
<script>
  window.API_BASE_URL = 'http://localhost:9000';
</script>
<script type="module" src="app.js"></script>
```

## Key features

- Animated sidebar with Browse, Installed, Blacklist, and Settings tabs.
- Thunderstore-powered browsing with search, mod details, and install progress indicator.
- Automatic handling of dependencies (excluding MelonLoader), uninstall on blacklist, and uninstall support.
- Local settings for the BONELAB install directory, persisted in `backend/data/state.json`.
- Update notifications with in-app and Windows-friendly toast support (via the backend endpoint for future integration).

## Notes

- The backend downloads and extracts mod archives directly into the configured BONELAB directory. Ensure you have backups before installing.
- MelonLoader dependencies are intentionally ignored per the requirements.
- State is persisted locally; delete `backend/data/state.json` to reset.
