# Compiler des paquets Alpine

Ce document explique comment compiler, ou recompiler les paquets Alpine de la station blanche.

## Créer un poste d'administrateur

- Installer une machine virtuelle Alpine Standard
- Créer un utilisateur `admin`
- Activer le dépôt `community` dans le fichier `/etc/apk/repositories`
- Exécuter la commande `# apk update`
- Installer `visudo` grâce à la commande `$ sudo apk add sudo`
- Ajouter l'utilisateur `admin` au groupe `sudoers` grâce à la commande `visudo`
- Installer le SDK Alpine avec la commande `$ sudo apk add alpine-sdk`
- Exécuter la commande `$ sudo addgroup admin abuild`
- Créer la paire de clés publique-privée avec la commande `$ abuild-keygen -a -i`
  - Donner le nom de fichier suivant lorsque demandé : `/home/admin/.abuild/panoptiscan.rsa`
- Installer git avec la commande `$ sudo apk add git`

## Avertissement

- La copie des paquets Alpine sur la VM de *build* Alpine doit être faite **impérativement** à l'aide de l'outil rsync et non l'outil scp car ce dernier perd les liens symboliques durant la copie.

## Compilation

- Cloner le dépôt Panoptiscan avec la commande : `$ cd ; git clone url_du_depot`
- Se rendre dans le dossier `~/Panoptiscan/setup/packages/panoptiscan`
- Choisir un paquet à construire et taper la commande `cd paquet_a_construire`
- Démarrer la compilation avec la commande `$ abuild -r`. 

### Instructions spécifiques

Cette section présente les instructions spécifiques à certains paquets.

## Publication

Avant de publier le dépôt, il faut signer le fichier d'index :
`$ à compléter`

Avant d'utiliser un dépôt sur une machine Alpine il faut installer la clé de signature du dépôt. Pour plus d'informations sur la génération de la clé, voir *Création du poste de build.md*.

La clé doit être copiée dans le dépôt de binaires Alpine avec les fichiers APK. Si l'utilisateur qui a construit les paquets est `admin`, la clé se trouve dans le dossier `/home/admin/.abuild/admin*.pub`.

## Test du dépôt

Editer le fichier `/etc/apk/repositories` et ajouter le chemin vers le nouveau dépôt.

Taper la commande `sudo apk update`, puis `echo $?`, la valeur affichée doit être 0?

## Configuration des paquets

Les paquets doivent être adaptés à l'infrastructure de déploiement :

### panoptiscan-common

#### chrony.conf

Modifier la valeur du serveur NTP. Valeur initiale : 192.168.10.253.
