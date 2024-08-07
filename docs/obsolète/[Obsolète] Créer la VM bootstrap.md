# Guide de création de la VM bootstrap pour la chaine CI

Les pipelines de création des images disque de déploiement doivent être exécutés sur un hôte dom0 préparé. Ce guide explique comment préparer l'hôte dom0.

## Livrable

Le livrable résultant de ce guide est une image disque au format VMDK.

## Pré-requis

Les opérations décrites dans ce guide doivent impérativement être réalisée sur une machine disposant d'un accès à Internet, direct ou derrière un proxy.

## Création d'une machine virtuelle

Les actions suivantes sont réalisées à partir de VMWare Fusion pour Mac OS. Elles doivent être adaptées pour un usage sur un logiciel différent.

- Créer une nouvelle machine virtuelle nommée Panoptiscan-base
- Fournir l'image ISO *alpine-xen-3.15.0-x86_64.iso* (ou autre version)
- Régler les paramètres de la machine virtuelle :
  - RAM : 8 Go
  - CPU : 2 CPU
    - Activer les fonctionnalités de virtualisation
  - Disque dur : 1 disque dur d'une taille de 32 Go au format VMDK **en un seul fichier**.
    - Nommer le disque `VM base Panoptiscan.vmdk`
  - Réseau : activer une interface réseau
- Démarrer la machine virtuelle, attendre l'invite de login `localhost login:`
- Taper `root` puis la touche entrée, l'invite `localhost:~#` s'affiche
- Taper `setup-alpine` puis la touche entrée
  - Si le clavier est configuré en qwerty, il faudra adapter la saisie
- Saisir les valeurs suivantes au questions posées :
  - *Select keyboard layout :* fr
  - *Select variant :* fr
  - *Enter hostname:* panoptiscan.local
  - *Which one do you want to initialize ? [eth0] :* eth0
  - *Do you want to bridge the interface eth0? (y/n) [y]* n
  - *Which one do you want to initialize? [br0]* eth0
  - *Ip address for eth0?:* dhcp
  - *Do you wan to do any amnual network configuration (y/n):* n
  - *New password :* saisir un nouveau mot de passe
  - *Retype password:* resaisir le nouveau mot de passe
  - *Which timezone are you in?:* Europe/Paris
  - *HTTP/FTP proxy URL?:* none (ou définir l'URL du proxy HTTP)
  - *Which NTP client to run ?:* busybox
  - *Enter mirror number (1-57):* r
  - *Which SSH server?:* openssh
  - *Which disk(s) would you like to use?:* sda
  - *How would you like to use it?:* sys
  - *WARNING : Erase the above disk(s) and continue?:* y
- L'installation s'achève par la phrase `Installation is complete. Please reboot.` et l'invite `panoptiscan:~#`est affichée.
- Taper `apk add sudo` puis la touche entrée
- Taper `visudo` puis la touche entrée
- Décommenter la ligne `# %wheel ALL=(ALL) NOPASSWD: ALL`
- Taper `:wq` puis la touche entrée  
- Taper `adduser admin` puis la touche entrée, et saisir deux fois le mot de passe
- Taper `addgroup admin wheel` puis la touche entrée
- Taper `apk update` puis la touche entrée
- Taper `apk upgrade` puis la touche entrée
***- Taper `apk add xen xen-hypervisor bridge`***
- Taper `xl list | grep Domain-0`
  - La ligne affichée devrait commencer par `Domain-0 0 384`
  - Dans le cas contraire, interrompre l'installation et contacter le support de niveau 2
- Taper `apk add dbus avahi` puis entrée
- Taper `rc-update add avahi-daemon default` puis entrée
//- Taper `apk add dnsmasq` puis entrée
//- Taper `rc-update add dnsmasq default` puis entrée
- Taper `halt` puis la touche entrée
- Se rendre dans le répertoire de données de la machine virtuelle et archiver le fichier panoptiscan-base.vmdk
- Fin de la procédure
