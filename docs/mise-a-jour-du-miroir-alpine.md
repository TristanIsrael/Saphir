# Créer ou mettre à jour le miroir Alpine

Cette documentation présente la mise en oeuvre des dépôts de paquets Alpine.

## Pré-requis

Pour réaliser cette procédure, les pré-requis suivants doivent être satisfaits :

- Serveur web existant avec un accès non sécurisé (pas de mot de passe ni certificat SSL) pour les *dépôts Alpine*

## Principes

Les dépôts sont faits pour évoluer dans le temps et permettre la MCO et la MCS de la distribution Alpine installée sur les stations blanches, mais aussi les logiciels du contrôleur (Panoptiscan) et les bases antivirales.

Lorsqu'un miroir est synchronisé depuis Internet, il faut conserver sa numération (par exemple 3.15.2) et établir un lien symbolique vers ce répertoire permettant à la fois d'utiliser systématiquement la dernière version des dépôts mais aussi d'utiliser une version spécifique lorsque c'est nécessaire (régression, tests, etc)

## Procédure

- Sur le serveur web, créer le répertoire racine des dépôts, par convention, nous appelerons cette racine [ALPINE] dans la suite de ce document.

- Dans le dossier [ALPINE], créer le sous-dossier`panoptiscan`.

- Dans le dossier [ALPINE], copier le dépôt Alpine officiel en conservant le nom de la version, par exemple 3.15.

- Créer un lien symbolique nommé `latest-stable` vers le dossier du dépôt officiel.

### Actions communes

Les mises à jour, même mineures, apportent presque toujours des modifications sur les noyau XEN et Linux. Ceux-ci doivent être mis à jour sur les dépôts mais aussi sur l'infrastructure de déploiement.

**Avant de mettre à jour un dépôt existant, il est recommandé d'en créer une copie et de la conserver pour pouvoir revenir sur celui-ci en cas de dysfonctionnement des stations blanches consécutif à la mise à jour. Voir ci-dessous :**

- Créer un nouveau répertoire portant le numéro exact de la version (3.15.5 et non 3.15) : 
```
$ cd [ALPINE]
$ cp -r 3.15.4 3.15.5

```

- Dans une ligne de commande shell, se placer dans le répertoire et commencer la mise à jour :
```
$ wget --mirror --no-parent https://dl-cdn.alpinelinux.org/alpine/v3.15/releases/x86_64/
```

>>> Créer un script de mise à jour automatisée

### Actions post-mise à jour

Après la mise à jour des dépôts, l'infrastructure de déploiement doit être mise à niveau. Pour ce faire, il suffit de rejouer le playbook ansible de déploiement (voir [Créer l'infrasructure de déploiement](creer-l-infrastructure-de-deploiement.md).
