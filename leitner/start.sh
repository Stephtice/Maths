#!/usr/bin/env bash
# Démarre l'appli Boîtes de Leitner (tables de multiplication).
# Usage : bash start.sh   (puis http://<ip-du-pi>:5000/leitner/)
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}" && pwd)"
cd "$APP_DIR"

if ! python3 -c "import flask" 2>/dev/null; then
  echo "==> Installation de Flask (pip --user)"
  pip3 install --user -r requirements.txt
fi

echo "==> Lancement sur le port ${PORT:-5000}"
echo "    URL locale : http://127.0.0.1:${PORT:-5000}/leitner/"
exec python3 app.py
