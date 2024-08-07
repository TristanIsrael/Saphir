# Description du socle

Ce document décrit l'architecture du socle technique orienté produits de sécurité.

## Machines virtuelles (domaines)

Le socle comporte les machines virtuelles suivantes :

| Nom | Description | Confiance |
|---|---|---|
| Dom0 | Le Domaine 0 est une machine virtuelle spéciale permettant de gérer les domaines utilisateur et l'interface avec le XenBus | Forte |
| vm-sys-usb | Ce domaine utilisateur a pour fonction de gérer les supports USB (clavier, souris, supports de stockage) et de les isoler du reste du système | Faible |
|  | |

### Dom0

Cette section fournit des détails techniques sur le `domaine 0`.

**La toolstack XEN doit être installée sur le Dom0. En principe elle est fournie par l'installation PXE lors du démarrage depuis le réseau**.

Paquets installés :
- python (`python3`)

### vm-sys-usb

Cette section fournit des détails techniques sur le domaine utilisateur `vm-sys-usb`.

Le domaine `vm-sys-usb` fournit les fonctions suivantes au travers du XenStore :
- saisie clavier
- position de la souris
- état des boutons de la souris
- position du toucher sur l'écran tactile
- lecture du catalogue des fichiers d'un support USB
- lecture d'un fichier depuis un support USB
- écriture d'un fichier sur un support USB.

Ressources :
| Ressource | Capacité |
|---|---|
| RAM | 400 Mo |

Paquets installés :
- python3
- py3-pyserial
- ntfs-3g 
- evtest (pour le développement uniquement) 
- py3-libevdev

Fichiers supprimés :
- aucun

#### Détection des supports USB

La détection des supports USB est prise en charge par `udev`. Une règle spécifique est ajoutée grâce au fichier `99-usbdisks.rules` placé dans le répertoire `/etc/udev/rules.d`.

Lorsqu'un support USB est connecté, le script `mdev-usb-storage` est exécuté. Celui-ci vérifie la présence du support et crée un point de montage dans `/media/usb` portant le même nom que le disque connecté. Ensuite, une notification est envoyée sur le Xenbus grâce à la messagerie.