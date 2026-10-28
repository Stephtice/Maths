# Site « Maths » sur Raspberry Pi

Héberger les applis maths sur votre propre Raspberry Pi, en accès libre
sur le réseau de la maison (ou de l'école).

## Étape 1 : préparer le Pi

Si ce n'est pas déjà fait, suivez les étapes 1 et 2 du guide du dépôt TDB
(`TDB/mon-appli-ecoles/raspberry/GUIDE.md`) : Raspberry Pi Imager, SSH activé,
connexion au Wi-Fi.

    ssh pi@raspberrypi.local

## Étape 2 : installer le site (~2 min)

    git clone https://github.com/Stephtice/Maths.git
    cd Maths
    bash raspberry/install.sh

Le site est servi par nginx sur le **port 8080**, en lecture directe
du dépôt : toute mise à jour via `git pull` est visible immédiatement,
sans redémarrage.

## Étape 3 : utiliser

Sur n'importe quel appareil du même réseau (téléphone, tablette, PC) :

    http://raspberrypi.local:8080

ou l'adresse IP affichée à la fin de l'installation
(ex. `http://192.168.1.42:8080`). Ajoutez-la à l'écran d'accueil
du téléphone pour un accès en une icône.

## En résumé sur le Pi

| Application | Port | Adresse |
|---|---|---|
| Mes Écoles (TDB) | 5000 | `http://raspberrypi.local:5000` |
| Maths | 8080 | `http://raspberrypi.local:8080` |

## Commandes de gestion

| Action | Commande |
|---|---|
| État | `systemctl status nginx` |
| Relancer | `sudo systemctl restart nginx` |
| Mettre à jour le site | `cd Maths && git pull` (rien d'autre à faire) |
| Journal | `journalctl -u nginx -f` |

## Accès depuis l'extérieur (au choix)

Comme pour l'application TDB : réseau privé via **Tailscale**
(`http://100.x.y.z:8080`) ou redirection de port sur la box
(`externe 8080 → IP_Pi :8080`). Voir le guide TDB, étape 4.
