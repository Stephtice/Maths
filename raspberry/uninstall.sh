#!/usr/bin/env bash
# Script de désinstallation du serveur Maths sur le Raspberry Pi.
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "ERREUR : lancez ce script avec sudo (sudo bash uninstall.sh)" >&2
  exit 1
fi

systemctl disable --now maths-apps.service 2>/dev/null || true
systemctl disable --now maths-apps-sync.service 2>/dev/null || true
rm -f /etc/systemd/system/maths-apps-sync.service
rm -f /etc/systemd/system/maths-apps-sync.timer
rm -f /usr/local/bin/maths-apps-sync.sh

systemctl daemon-reload
systemctl restart lighttpd 2>/dev/null || true
rm -rf /opt/maths-apps
echo "✅ Serveur Maths supprimé. lighttpd reste installé (sudo apt remove lighttpd pour le retirer)."
