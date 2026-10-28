#!/usr/bin/env bash
# Installation des applis Maths sur un Raspberry Pi.
# Usage : bash install.sh
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVE_DIR="/opt/maths-apps"
SERVICE_NAME="maths-apps"
PI_USER="${PI_USER:-$USER}"

echo "==> Déploiement des applis Maths pour le Raspberry Pi"

if [ "$(id -u)" -ne 0 ]; then
  echo "ERREUR : lancez ce script avec sudo (sudo bash install.sh)" >&2
  exit 1
fi

echo "==> Mise à jour des paquets et installation de git + lighttpd"
apt-get update
apt-get install -y git lighttpd

echo "==> Préparation de ${SERVE_DIR}"
mkdir -p "${SERVE_DIR}"
chown -R "${PI_USER}:${PI_USER}" "${SERVE_DIR}"

echo "==> Copie des fichiers (sauf raspberry/)"
rsync -a --delete --exclude='.git' --exclude='raspberry' "${APP_DIR}/" "${SERVE_DIR}/"
chown -R "${PI_USER}:${PI_USER}" "${SERVE_DIR}"

echo "==> Configuration de lighttpd sur le port 8080"
sed -i "s/^server.port[[:space:]]*=.*/server.port = 8080/" /etc/lighttpd/lighttpd.conf
sed -i "s|^server.document-root[[:space:]]*=.*|server.document-root = \"${SERVE_DIR}\"|" /etc/lighttpd/lighttpd.conf
rm -f /etc/lighttpd/conf-enabled/50-maths-apps.conf /etc/lighttpd/conf-available/50-maths-apps.conf

echo "==> Configuration de la synchro automatique depuis GitHub"
cat > /usr/local/bin/maths-apps-sync.sh <<EOF
#!/usr/bin/env bash
# Synchronise les applis depuis GitHub puis rafraîchit le dossier servi.
set -euo pipefail
REPO_URL="\${MATHS_REPO_URL:-https://github.com/Stephtice/Maths.git}"
TMP_DIR="\$(mktemp -d)"
trap 'rm -rf "\${TMP_DIR}"' EXIT
git clone --depth 1 "\${REPO_URL}" "\${TMP_DIR}/repo"
rsync -a --delete --exclude='.git' --exclude='raspberry' "\${TMP_DIR}/repo/" "${SERVE_DIR}/"
logger -t maths-apps "Synchronisation GitHub terminée"
EOF
chmod 755 /usr/local/bin/maths-apps-sync.sh

echo "==> Service systemd lighttpd activé (léger, démarrage auto, redémarrage après coupure)"
systemctl enable lighttpd

cat > "/etc/systemd/system/${SERVICE_NAME}-sync.service" <<EOF
[Unit]
Description=Synchro des applis Maths depuis GitHub
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/maths-apps-sync.sh
EOF

cat > "/etc/systemd/system/${SERVICE_NAME}-sync.timer" <<EOF
[Unit]
Description=Synchro des applis Maths toutes les 15 minutes

[Timer]
OnCalendar=*:0/15
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl restart lighttpd
systemctl enable --now "${SERVICE_NAME}-sync.timer"

IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
echo ""
echo "✅ Installation terminée."
echo "   Accueil des applis : http://${IP:-<ip-du-pi>}:8080/"
echo "   Applis : TRIO, Dobble Éclair, Organiser les cubes, 15 gagne"
echo "   La synchro GitHub tourne toutes les 15 min (maths-apps-sync.timer)."
