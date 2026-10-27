# Documentation d'intégration

Ce document permet à l'intégrateur de réaliser les actions visant à construire une configuration de station blanche Panoptiscan

## Configurations matérielles

Les configurations actuelles sont :

- `S raspi` basée sur une architecture ARM avec une carte Raspberry Pi 4B

- `S latte` panda basée sur une architecture x86 avec une carte Latte Panda Delta

- `XL` basée sur une architecture x86 avec un PC standard

## Configurations logicielles

Les configurations logicielles peuvent être multiples au gré des besoins de l'intégrateur. Les configurations connues sont décrites dans les sections suivantes.

### S MVP (juin 2022)

Cette configuration est compatible avec les configurations matérielles suivantes : S raspi. 

Fichier de configuration : `s-mvp.tar.gz`.

La sélection de la configuration est faite lors de l'initialisation de second niveau, dans le fichier `/var/tftpboot/cmdline.txt` hébergé sur le serveur TFTP.

### XL MVP (juin 2022)

Cette configuration est compatible avec les configurations matérielles suivantes : XL. 

La sélection de la configuration est faite durant la phase de boot iPXE, dans le fichier `/var/www/pxe/gpxe-script` hébergé sur le serveur HTTP.

Fichier de configuration : `xl-mvp.tar.gz`.

## Outils

Les outils suivants sont nécessaires :

- Un PC ou une machine virtuelle vierge connecté au réseau de déploiement Panoptiscan

## Composants

Les composants à installer sur une station blanche Panoptiscan sont :

- Serveur X (xorg) *installé par le paquet panoptiscan-mvp*

- Clamav avec freshclam *installé par le paquet panoptiscan-mvp*

- Python 3 et dépendances *installé par le paquet panoptiscan-mvp*

- Outils divers *installés par le paquet panoptiscan-mvp*

- L'interface graphique de contrôle *installée par le paquet panoptiscan-mvp*

## Etapes

Une ou plusieurs étapes peuvent être nécessaires pour mettre à jour l'infrastructure de déploiement des stations blanches.

L'intégrateur suivra une ou plusieurs des étapes suivantes en fonction de la situation.

### Mise à jour du miroir du dépôt Alpine

Les paquets du dépôt officiel Alpine sont mis à jour régulièrement afin d'apporter des corrections aux différents outils proposés (MCO et MCS).

Il est reconmandé de mettre à jour hebdomadairement les paquets en suivant la *procédure de mise à jour du miroir Alpine*.

Lorsque le dépôt à été mis à jour, les dernières versions de paquets seront automatiquement disponibles et consommées par les stations blanches lors de leur démarrage par le réseau. S'il s'agit de stations blanches nomades, il est recommandé de suivre la procédure de *création d'une station blanche nomade*.
