# Compiler le noyau Alpine Linux

Cette documentation explique comment recompiler le noyau Linux Alpine.

Pourquoi recompiler le noyau Alpine ? Principalement pour les raisons suivantes :

- obtenir les meilleures performances sur les stations blanches portables

- obtenir la meilleure sécurité en réduisant la surface d'attaque, par la désactivation des modules et fonctionnalités non-nécessaires

- corriger certains problèmes d'intégration liés aux noyaux compilés fournis dans la distribution officielle (manque af_packet, e1000, usbip-*)

>>> Question : le noyau n'est-il pas déjà suffisamment restreint et peut-on se contenter de blacklister les modules ? -> question à poser à SDCYB.

## Pré-requis

*Il ne faut pas utiliser les sources officielles de Linux directement, elles seront téléchargées automatiquement*

- Poste de build Alpine préparé
  - Les dépôts Alpine doivent être configurés sur la version à laquelle appartient le noyau. Par exemple, pour recompiler le noyau de la version 3.15.5, il faut placer les dépôts sur la version 3.15 d'Alpine.
  - Mettre à jour le système avec la commande `apk update && apk upgrade`

- Connexion à Internet

## Procédure

*Adapter les versions d'Alpine en fonction des besoins*

- Se connecter au poste de build Alpine

- Taper les commandes suivantes :
```
$ cd 
$ git clone https://gitlab.alpinelinux.org/alpine/aports.git
$ git checkout tags/v3.15.5
$ cd main/linux-lts
$ abuild clean cleancache cleanoldpkg cleanpkg
$ abuild checksum
$ abuild -rK

```