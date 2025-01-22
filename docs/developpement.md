# Développement de Saphir

Ce document présente la mise en oeuvre d'un environnement de développement pour Saphir.

## Technologies

Les technologies, outils et dépendances mis en oeuvre dans Saphir sont :
- Alpine Linux >= v3.20
- Dépôt de binaires Alpine Linux
- Serveur DHCP
- Python 3
- Qt >= 6.5 (PySide6)
- PSEC (*Platform Security Enhanced Core*)
- Visual Studio Code
- Mosquitto

## Pré-requis 

Le développement de Saphir nécessite les pré-requis suivants :
- Le système d'exploitation pour le développement devrait être de préférence un système dérivé d'Unix (GNU/Linux, MacOS, ...)
- Python 3
- Visual Studio Code installé avec les plugins pour le codage et le débogage sous python
- Broker Mosquitto >= 2.0
- ClamAV (`clamd`)
- PSEC doit être disponible dans le PATH (soit le code source, soit la bibliothèque python)

## Dépendances

Les dépendances sont gérées directement dans les paquets Alpine du produit et dans les fichiers `requirements.txt`.

## Installation initiale

*Les étapes suivantes correspondent à une installation sur un ordinateur équipé de Debian Linux 12 nouvellement installé.*

- installer `python` et `pip`: `$ sudo apt install python3 python3-pip` 
- installer `mosquitto` : `$ sudo apt install mosquitto`
- installer `clamav` : `$ sudo apt install clamav clamav-daemon`
- installer des dépendances spécifiques : `$ sudo apt install libxcb-cursor-dev libxcb-cursor0 libxcb-keysyms1 libxkbcommon-x11-0 libxcb-xinerama0 libxcb-xinput0 libxcb-icccm4`
- créer un répertoire de travail et s'y déplacer : 
```
$ cd 
$ mkdir workspace
$ cd workspace 
```
- installer le module `venv` : `$ sudo apt install python-3.11-venv`
- créer un environnement virtuel : `$ python3 -m venv venv`
  - entrer dans l'environnement : `$ . venv/bin/activate`
- installer le module `PSEC` : `$ pip install ./psec-1.0-py3-none-any.whl`
  - les dépendances sont installées automatiquement : `humanize, joblib, etc`
- décompresser le dossier source de Saphir
- entrer dans le répertoire `python/gui/src/Saphir`
- installer les dépendances : `pip install -r requirements.txt`

Après ces étapes l'environnement virtuel python pour `Saphir` est disponible et peut-être utilisé tel quel en ligne de commande ou dans Visual Studio Code.

### Notes

Si vous utilisez Visual Studio Code, l'environnement est déjà configuré dans les fichiers `.vscode/*`. 
En ligne de commande il faut définir la variable d'environnement `PYTHONPATH` : `$ PYTHONPATH=.:../../../libsaphir/src python3 main.py`.

**En environnement de développement la variable d'environnement `DEVMODE=True` doit toujours être définie. Exemple : `DEVMODE=True PYTHONPATH=.:../../../libsaphir/src python3 main.py`**

## Architecture

En développement, l'architecture de Saphir utilise plusieurs bouchons pour simuler certaines interactions avec l'environnement. Les fonctions système sont fournies par `PSEC`, notamment les échanges de fichier et les mécanismes de communication inter-processus et de messagerie. Certaines de ces fonctions sont *mockées* dans l'environnement de développement pour augmenter la maîtrise des tests.

L'élément central de l'orchestration des IPC et des messages est le broker Mosquitto.

Les fichiers sont fournis, au travers de `PSEC`, par la classe `MockSysUsbController` qui simule la machine virtuelle qui fournit l'interface avec les supports USB.

L'analyse antivirale est fournie par la classe `MockClamAntivirusController` qui permet l'intégration de ClamAV avec le système sous test.

## Préparation

- Un broker Mosquitto doit être disponible sur le port standard `tcp/1883`.
- ClamAV `clamd` doit être démarré et accessible au travers d'une socket de domaine Unix (paramètre `LocalSocket` dans le fichier `clamd.conf`).
- Les fonctions du fichier `DevModeHelper.py` doivent être ajustées en fonction de l'environnement local :
  - `get_mocked_source_disk_path()` retourne le chemin du dossier qui sera utilisé comme support USB source. Dans l'idéal ce dossier devrait contenir une arborescence complexe à plus de 10 niveaux et contenant plusieurs milliers de fichiers. Les fichiers doivent être accessibles en lecture.
  - `get_mocked_destination_disk_path()` retourne le chemin du dossier qui sera utilisé comme support USB de sortie.
  - `get_storate_path()` retourne le chemin du dossier qui sera utilisé comme dépôt local pour les transferts. Ce doit être un dossier spécifique à l'utilisateur, dans l'idéal un dossier temporaire.
- En production il faut 2 antivirus, or en développement nous n'en avons qu'un. Il faut donc régler la constante `ANTIVIRUS_NEEDED` du fichier `_constants.py` dans `libsaphir` à `1`. 

## Mise en route

Si le broker Mosquitto est démarré, exécuter le fichier `MockSysUsbController.py` pour démarrer le simulateur de la machine virtuelle USB.

Ensuite, démarrer la GUI en exécutant le fichier `main.py`. **Le paramètre `DEVMODE=True` doit être fourni sur la ligne de commande de l'application**.

Enfin, démarrer l'interface avec l'antivirus en exécutant le fichier `MockClamAntivirusController.py`.

*Démarrer l'antivirus tardivement permet de constater les changements d'état dans la GUI. Celle-ci ne passera à l'état PRET que si tous les composants sont démarrés et disponibles.*.

## Mode d'affichage

En production l'application est démarrée en plein écran et son usage est exclusif, il n'est pas possible d'utiliser une autre application. En développement, celle-ci peut être affichée en plein écran ou en fenêtre selon les besoins du développeur.

Le choix du mode d'affichage est fait en modifiant la valeur de la constante `FORCE_FULLSCREEN` dans le fichier `main.py`.
