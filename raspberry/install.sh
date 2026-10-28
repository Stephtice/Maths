#!/bin/bash
# Installation du site Maths sur Raspberry Pi
# A lancer a la racine du depot : bash raspberry/install.sh
set -e

echo "=== Installation Maths sur Raspberry Pi ==="

if [ ! -f index.html ]; then
    echo "ERREUR : lancez ce script depuis la racine du depot Maths."
    echo "  cd Maths && bash raspberry/install.sh"
    exit 1
fi

REPO_DIR=$(pwd)

# Dependances systeme : nginx sert les fichiers statiques
sudo apt-get update -qq
sudo apt-get install -y -qq nginx

# Fichiers du site lisibles par nginx
chmod -R o+rX "$REPO_DIR"

# Site nginx : port 8080, racine = ce depot
sudo tee /etc/nginx/sites-available/maths > /dev/null <<EOF
server {
    listen 8080;
    listen [::]:8080;
    server_name _;
    root $REPO_DIR;
    index index.html;
    location / {
        try_files \$uri \$uri/ =404;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/maths /etc/nginx/sites-enabled/maths
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=== Installation terminee ==="
echo "Site Maths en cours : http://${IP}:8080"
echo "(nginx redemarre automatiquement a chaque allumage du Pi)"
echo "Sur le reseau local : http://raspberrypi.local:8080"
echo ""
echo "Mise a jour apres un git pull : rien a faire, nginx sert les fichiers en direct."
