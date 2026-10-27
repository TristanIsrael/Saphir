# Description des domaines

Ce document donne la description précise des différents domaines du système/

## Dom0

Ce chapitre présente l'organisation du Dom0.

### Fichiers

Les fichiers sont organisés de façon ordonnée sur le Dom0 :

| Répertoire/Fichier | Contenu | Partage DomU |
|---|---|---|
| /etc/xen/panoptiscan | Contient les définitions des machines virtuelles XEN | Non |
| /var/log/panoptiscan.log | Fichier journal aggrégé pour tout le système | Non |
| /usr/local/panoptiscan | Contient l'ensemble des fichiers binaires du projet | |
| /usr/local/panoptiscan/depot | Contient les paquets d'installation Alpine pour les DomU | `depot` |
| /usr/local/panoptiscan/scripts | Contient des scripts utilisés par les DomU | `scripts` |

## vm-sys-usb

Ce chapitre présente l'organisation du Domaine `vm-sys-usb`.

### Points de montage

| Nom du partage | Point de montage | Description |
|---|---|---|
| scripts | /mnt/scripts | Contient les scripts shell et python nécessaires au fonctionnement du domaine |
| alpine | /mnt/alpine | Contient les paquets d'installation Alpine nécessaires à l'initialisation du domaine |
| depot | /mnt/depot | Contient les fichiers transférés depuis et vers les supports USB |
| tmp | /mnt/tmp | Contient des fichiers de test *uniquement en mode Debug* |

### Canaux PV

| Chemin de la socket | Type de socket | Description |
|---|---|---|
| /dev/hvc0 | tty | Canal réservé à la console Xen |
| /dev/hvc1 | RS232 | Canal réservé à la messagerie |
| /dev/hvc2 | RS232 | Canal réservé à la journalisation des événements |

### Modules de noyaux

Les modules suivants sont nécessaires au fonctionnement du domaine :

| Nom du module | Usage |
|---|---|
| 9p | Permet le montage du système de fichier 9p XEN |
| 9pnet | Permet l'utilisation du réseau pour le système de fichier 9p |
| 9pnet_xen | Permet l'utilisation du Xenbus pour le système de fichier 9p |
| netfs | Permet l'utilisation d'un système de fichier réseau |