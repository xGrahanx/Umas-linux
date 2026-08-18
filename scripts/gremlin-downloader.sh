#!/bin/bash
# Universal launcher for Gremlin Downloader

# ---- move to project root directory --------------------------------
SCRIPT_DIR="$(dirname $(realpath "$0"))"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# ---- detect Python environment -------------------------------------
export PATH=$PATH:$HOME/.local/bin
PYTHON=""

if [ -d "venv" ]; then
    PYTHON="./venv/bin/python"
elif command -v uv >/dev/null 2>&1; then
    PYTHON="uv run python"
else
    PYTHON="python3"
fi

# ---- use xcb in wayland --------------------------------------------
if [ "${XDG_SESSION_TYPE}" = "wayland" ]; then
    export QT_QPA_PLATFORM=xcb
fi

# ---- launch gremlin downloader -------------------------------------
$PYTHON -m src.asset_downloader_gui
