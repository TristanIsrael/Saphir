# API Python

Ce document décrit le fonctionnement de l'API Python.

## Emplacement des fichiers

Certains fichiers ont un emplacement fixe, ou faisant l'objet d'un paramètre :

| Fichier | Description | Paramètre | Valeur par défaut | Commentaire |
|---|---|---|---|---|
| Fichier journal | Fichier journal local au domaine | CHEMIN_JOURNAL_LOCAL | /var/log/panoptiscan.log | Le fichier n'est créé que si le paramètre ACTIVE_JOURNAL_LOCAL est à True |
| Bibliothèque python | La bibliothèque contient toutes les classes Python nécessaires au fonctionnement du système | Aucun | Dossier python du système | La bibliothèque est packagée dans le fichier panoptiscan_lib[...]-none-any.whl et est installée automatiquement lors du déploiement du système |
| Socket messagerie DomU | Les sockets de communication avec chaque DomU sont stockées au même endroit. | CHEMIN_SOCKETS_MSG | /var/run/panoptiscan/*-msg.sock | |
| Socket journal DomU | Les sockets de journalisation avec chaque DomU sont stockées au même endroit. | CHEMIN_SOCKETS_LOG | /var/run/panoptiscan/*-log.sock | |
| Paramètres globaux | Les paramètres définissent le comportement des composants python | CHEMIN_FICHIER_CONFIG_GLOBAL | /etc/panoptiscan/global.conf | |

## Packaging

