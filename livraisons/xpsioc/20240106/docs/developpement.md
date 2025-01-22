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

## Architecture

En développement, l'architecture de Saphir utilise plusieurs bouchons pour simuler certaines interactions avec l'environnement. Les fonctions système sont fournies par `PSEC`, notamment les échanges de fichier et les mécanismes de communication inter-processus et de messagerie. Certaines de ces fonctions sont *mockées* dans l'environnement de développement pour augmenter la maîtrise des tests.

L'élément central de l'orchestration des IPC et des messages est le broker Mosquitto.

Les fichiers sont fournis, au travers de `PSEC`, par la classe `MockSysUsbController` qui simule la machine virtuelle qui fournit l'interface avec les supports USB.

L'analyse antivirale est fournie par la classe `MockClamAntivirusController` qui permet l'intégration de ClamAV avec le système sous test.

## Préparation

- Un broker Mosquitto doit être disponible sur le port standard `tcp/1883`.
- ClamAV `clamd` doit être démarré et accessible au travers d'une socket Unix.
- Les fonctions du fichier `DevModeHelper.py` doivent être ajustées en fonction de l'environnement local :
  - `get_mocked_source_disk_path()` retourne le chemin du dossier qui sera utilisé comme support USB source. Dans l'idéal ce dossier devrait contenir une arborescence complexe à plus de 10 niveaux et contenant plusieurs milliers de fichiers. Les fichiers doivent être accessibles en lecture.
  - `get_mocked_destination_disk_path()` retourne le chemin du dossier qui sera utilisé comme support USB de sortie.
  - `get_storate_path()` retourne le chemin du dossier qui sera utilisé comme dépôt local pour les transferts. Ce doit être un dossier spécifique à l'utilisateur, dans l'idéal un dossier temporaire.

## Mise en route

Si le broker Mosquitto est démarré, exécuter le fichier `MockSysUsbController.py` pour démarrer le simulateur de la machine virtuelle USB.

Ensuite, démarrer la GUI en exécutant le fichier `main.py`. **Le paramètre `DEVMODE=True` doit être fourni sur la ligne de commande de l'application**.

Enfin, démarrer l'interface avec l'antivirus en exécutant le fichier `MockClamAntivirusController.py`.

*Démarrer l'antivirus tardivement permet de constater les changements d'état dans la GUI. Celle-ci ne passera à l'état PRET que si tous les composants sont démarrés et disponibles.*.

## Mode d'affichage

En production l'application est démarrée en plein écran et son usage est exclusif, il n'est pas possible d'utiliser une autre application. En développement, celle-ci peut être affichée en plein écran ou en fenêtre selon les besoins du développeur.

Le choix du mode d'affichage est fait en modifiant la valeur de la constante `FORCE_FULLSCREEN` dans le fichier `main.py`.
