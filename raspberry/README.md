# Raspberry Pi — serveur des applis Maths

Le Raspberry Pi héberge **toutes les applis** du dépôt (TRIO, Dobble Éclair, Organiser les cubes, 15 gagne) et les maintient à jour automatiquement depuis GitHub.

## Ce que fait l'installation

- Installe `git` et `lighttpd` (serveur web léger, idéal sur Pi).
- Copie les applis dans `/opt/maths-apps` (le dossier `raspberry/` n'est pas servi).
- Sert les applis sur le **port 8080** via le service `lighttpd` (démarrage automatique au boot, redémarrage après coupure de courant).
- Crée un timer `maths-apps-sync` : **toutes les 15 minutes**, les applis sont re-synchronisées depuis GitHub (`main`). Chaque push sur `main` est donc visible sur le Pi dans le quart d'heure.

## Installation

Sur le Raspberry Pi (Raspberry Pi OS), avec le dépôt cloné ou copié :

```bash
git clone https://github.com/Stephtice/Maths.git
cd Maths/raspberry
sudo bash install.sh
```

Ensuite, depuis un appareil de la classe sur le même réseau :

```
http://<ip-du-pi>:8080/
```

(l'IP s'affiche à la fin de l'installation ; `hostname -I` sur le Pi pour la retrouver)

## Commandes utiles

```bash
systemctl status lighttpd               # état du serveur
sudo systemctl restart lighttpd         # redémarrer le serveur
sudo systemctl start maths-apps-sync.service  # forcer une synchro GitHub immédiate
journalctl -u lighttpd -e              # logs du serveur
```

## Réseau

Le serveur n'écoute que sur le réseau local du Pi : les applis sont accessibles uniquement depuis le réseau de la classe (pas d'exposition Internet).

## Désinstallation

```bash
cd Maths/raspberry
sudo bash uninstall.sh
```
