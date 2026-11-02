# Boîtes de Leitner — Tables de multiplication

Application Flask + SQLite pour mémoriser les tables de multiplication de 1 à 10
avec la méthode des boîtes de Leitner.

- **Inscription / connexion** : chaque élève a un compte (pseudo + mot de passe).
- **5 boîtes** : une bonne réponse fait monter la carte d'une boîte (jusqu'à la
  boîte 5 = apprise), une mauvaise réponse la fait retomber en boîte 1.
- **Répétition espacée** : les révisions sont espacées (0, 1, 2, 4, 8 jours selon la boîte).
- **Progrès sauvegardés** : base SQLite (`leitner.db`), un compte garde ses cartes
  et leurs boîtes d'un jour sur l'autre.

## Lancement local

```bash
cd leitner
bash start.sh          # installe Flask si besoin, lance sur le port 5000
```

Puis ouvrir `http://127.0.0.1:5000/`.

## Sur le Raspberry Pi (avec les autres applis Maths)

L'appli est servie sous `/leitner/` par le serveur existant : lancer le script
Flask en arrière-plan, par exemple via un service systemd `leitner.service`
(`ExecStart=/usr/bin/python3 /opt/maths-apps/leitner/app.py`, port 5000), puis
ajouter dans la config lighttpd :

```
server.modules += ("mod_proxy")
$HTTP["url"] =~ "^/leitner/" { proxy.server = (("" => (("host" => "127.0.0.1", "port" => 5000)))) }
```

L'URL devient alors `http://<ip-du-pi>:8080/leitner/`.

## Variables d'environnement

- `LEITNER_DB` : chemin de la base SQLite (défaut : `leitner.db` à côté de `app.py`)
- `LEITNER_SECRET_KEY` : clé de session Flask (générée aléatoirement sinon)
- `PORT` : port d'écoute (défaut : 5000)
