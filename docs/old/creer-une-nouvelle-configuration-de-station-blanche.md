# Création d'une nouvelle configuration

Cette documentation explique comment créer une nouvelle configuration pour une station blanche. Il peut s'agir de la toute première configuration des stations blanches, ou bien d'une nouvelle configuration permettant de prendre en compte un nouveau matériel ou une évolution logicielle.

## Identification d'une configuration

Les configurations (matérielle + logicielle) sont identifiées grâce aux arguments du noyau Linux qui est chargé pendant la phase de boot PXE (ou de boot local pour une version nomadisée).

Pour connaître la configuration courante il faut consulter le contenu du fichier `/proc/cmdline` qui est une copie exacte du fichier chargé pendant le boot.

La clé codant la configuration est `PANOPTISCAN_CONFIG`. Elle peut apparaître plusieurs fois dans la ligne de commande pour indiquer les différents aspects de la configuration.

Exemples :
```
PANOPTISCAN_CONFIG=xl           # Indique la configuration matérielle XL
PANOPTISCAN_CONFIG=s_raspi4B    # Indique la configuration matérielle S avec Raspberry Pi 4B
PANOPTISCAN_CONFIG=mvp_1        # Indique la configuration logicielle MVP en version 1
PANOPTISCAN_CONFIG=nomade       # Indique la configuration nomadisée
```

## Stockage des configurations

Toutes les configurations sont stockées sur le serveur HTTP/NFS de l'infrastructure de démarrage par le réseau (boot PXE). il s'agit de fichiers .tar.gz contenant une sauvegarde des fichiers du dossier /etc d'une installation Alpine.

Une configuration est créée grâce à la commande Alpine `lbu pkg`.

Lorsqu'une machine démarre par le réseau, elle charge sa configuration depuis le serveur HTTP et appliques le modifications, ce qui a pour conséquence de télécharger les paquets Alpine nécessaires.

### Création de configurations multiples

Pour gérer de multiples configurations il est nécessaire de définir des règles de différenciation entre les stations blanches et de les implanter dans le serveur DHCP. Une fois les critères établis et la différenciation faite, la station blanche pourra télécharger l'une ou l'autres des configurations créées.

Une prochaine mise à jour de cette documentation expliquera comment créer des configurations multiples pour cibler différents matériels, différents niveaux de confidentialité ou encore comment réaliser une pré-production des stations blanches.

Une configuration de station blanche correspond à une instantané d'une machine et des paramètres qui lui ont été appliqués. L'instantané prend la forme d'un petit fichier .tar.gz sauvegardé sur le serveur HTTP/NFS de l'infrastructure de déploiement.

Le fichier de configuration contient l'ensemble des fichiers du répertoire /etc de la machine au moment où l'instantané est créé.

Le nommage du fichier permet de gérer plusieurs configurations *en principe*. Cependant, dans la version actuelle, seul le fichier *default.tar.gz* est téléchargé lors du démarrage réseau par PXE. On ne peut donc gérer qu'une seule configuration.

## Scénario de création

### Nouvelle configuration

Dans la version actuelle, toute machine qui démarre par le réseau utilise une configuration unique nommée 'default'. Pour créer une nouvelle configuration, il faut supprimer ou renommer le fichier default.tar.gz dans le serveur HTTP/NFS, dans le dossier [racine web]/configs. 

Il est recommandé **de réaliser une sauvegarde du fichier de configuration avant toute modification de celle-ci**.

Si une

- Préparer une machine vierge

- Connecter la machine sur le réseau Panoptiscan

- Démarrer par le réseau

- Attendre l'affichage de l'invite de login Alpine

- Taper `root` puis Entrée

- Taper `setup-keymap` puis Entrée

- Taper `fr`puis Entrée

- Taper `fr`puis Entrée

- Editer le fichier `/etc/pak/repositories` et remplacer son contenu par :
```
http://[Adresse IP du dépôt Alpine]/alpine/latest-stable/main/
http://[Adresse IP du dépôt Alpine]/alpine/latest-stable/community/
http://[Adresse IP du dépôt Panoptiscan]/panoptiscan/
```

- Faire confiance au dépôt Panoptiscan en tapant les commandes suivantes :
```
# cd /etc/apk/keys
# wget http://[Adresse IP du dépôt Panoptiscan]/panoptiscan/panoptiscan.rsa.pub
# apk update
```

- Si la commande affiche l'erreur `UNTRUSTED SIGNATURE`, vérifier le fichier /etc/apk/keys/panoptiscan.rsa.pub et vérifier que le fichier panoptiscan.rsa.pub hébergé sur le dépôt Panoptiscan est bien celui qui a été utilisé pour signer les paquets Alpine du dépôt.

- Télécharger le script de mise à jour de la configuration en tapant les commandes suivantes :
```
# cd /tmp
# wget http://[Adresse IP du serveur HTTP/NFS]/save-config.sh
# chmod +x save-config.sh
```

- Installer les paquets et préparer la machine comme désiré

- Lorsque la configuration est correcte, taper la commande `sh /tmp/save-config.sh`

- La configuration est enregistrée sur le serveur

### Modification d'une configuration existante

Pour modifier une configuration existante, suivre les étapes suivantes :

- Démarrer une station blanche sur la configuration souhaitée

- Effectuer les modifications sur la station blanche (installation/suppression de paquets ou modifications de réglages)

- Lorsque la configuration est correcte, taper la commande `sh /tmp/save-config.sh`

- La configuration est enregistrée sur le serveur

## Historique des configurations

Le tableau ci-dessous indique les configurations connues :

| Nom | Création | Suppression | Description | Paquets |
|-----|----------|-------------|-------------|--------|
| MVP | juin 2022 | | Produit minimum viable sans durcissement | panoptiscan-common, panoptiscan-clamav, panoptiscan-controleur, panoptiscan-nomade, panoptiscan-rpi4 |
| v2 | juillet 2022 | | Version durcie avec hyperviseur XEN | panoptiscan-dom0 |
