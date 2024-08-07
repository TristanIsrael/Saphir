# Créer le serveur PXE

Le boot PXE permet de démarrer une station blanche par le réseau pour :

- l'utiliser directement

- préparer un appareil vièrge pour le nomadisme.

Cette documentation explique les étapes de mise en place de l'environnement permettant le boot PXE.

## Architecture réseau

Les services mis en oeuvre sont :

- Serveur DHCP - il fournit l'adresse IP et les détails pour le boot PXE au dispositif vierge.

- Serveur TFTP - il permet au dispositif vierge de télécharger les éléments de base nécessaires à la séquence de boot (noyau iPXE).

- Serveur HTTP - il permet au dispositif vierge de télécharger le noyau et initramfs linux ainsi que les paquets d'installation Alpine (APK) et la configuration initiale de la machine.

- Serveur NFS - il permet de stocker les configurations réalisées sur les différentes cibles (S, XL et configurations spéciales). Ce serveur n'est utile que pendant la phase de réalisation ou de mise à jour des configurations.

## Séquence de démarrage détaillée

La séquence de démarrage se déroule ainsi :

*le dispositif doit être branché sur un réseau (ou VLAN) ayant accès aux serveurs décrits ci-dessus.*

- alluumage du dispositif

- recherche de serveur DHCP

- obtention d'une adresse IP et récupération des informations pour le boot PXE (URL de téléchargement du noyau iPXE)

- téléchargement du noyau iPXE (gpxe.kpxe)

- boot sur le noyau iPXE

  - téléchargement du script gpxe-script qui fournit les informations sur le noyau Linux à démarrer

  - téléchargement du noyau Linux et de l'initramfs

  - boot sur le noyau Linux avec les arguments indiqués dans le script gpxe-script

    - chargement des modules indiqués dans le script gpxe-script

    - chargement du système

    - chargement de la configuration propre au dispositif

    - chargement et installation des paquets APK conformément à la configuration

    - démarrage des services et des scripts

- fin de la séquence

## Configuration des serveurs

### DHCP

Le serveur DHCP doit être configuré pour fournir l'adresse IP et la configuration de boot PXE pour le fichier gpxe.kpxe.

Si le serveur DHCP est installé spécifiquement, voici un exemple de configuration pour le serveur ISC DHCP :

```
default-lease-time 600;
max-lease-time 7200;

allow booting;

# in this example, we serve DHCP requests from 192.168.0.(3 to 253)
# and we have a router at 192.168.0.1
subnet 192.168.0.0 netmask 255.255.255.0 {
  range 192.168.0.3 192.168.0.253;
  option broadcast-address 192.168.0.255;
  option routers 192.168.0.1;
  option domain-name-servers 192.168.0.1;
  filename "gpxe.kpxe";
}

group {
  next-server 192.168.0.2;
  host tftpclient {
    filename "gpxe.kpxe";
  }
}
```

### Dépôt de fichiers PXE

Un dépôt de fichiers unique doit exister. Celui-ci sera utilisé par les serveurs TFTP, HTTP et NFS pour lire et écrire les données.

Plusieurs configurations sont envisageables

- Placer tous les services sur une machine unique et utiliser un répertoire commun comme dépôt de fichiers.

- Utiliser un serveur de données (CIFS, NFS, ...) comme dépôt de fichiers et créer un point de montage sur chacune des machines hébergant les services.

Le dépôt de fichiers doit contenir les dossiers suivants :

```
    configs/
    data/
    scripts/
```

Télécharger les fichiers de boot Alpine :
```
wget http://nl.alpinelinux.org/alpine/v3.15/releases/x86_64/netboot/vmlinuz-virt
wget http://nl.alpinelinux.org/alpine/v3.15/releases/x86_64/netboot/modloop-virt
wget http://nl.alpinelinux.org/alpine/v3.15/releases/x86_64/netboot/initramfs-virt
```

### TFTP

Installer un serveur tftp et le configurer pour servir les fichiers du dépôt indiqué ci-dessus.

### HTTP

Deux configurations sont envisageables :

- Avoir un serveur HTTP unique pour l'ensemble des fichiers (paquets APK et configurations PXE)

- (préférable) Avoir un serveur HTTP pour les paquets APK (DECOS) et un autre pour les configurations PXE.

Les paquets APK doivent être disponibles dans le DECOS idéalement. Dans tous les cas les paquets doivent être disponibles sur un serveur HTTP sous la forme d'un mirroir des dépôts officiels *main* et *community*.

En résumé l'un des serveurs HTTP doit servir les fichiers APK et l'autres les fichiers du dépôt de fichiers.

### NFS

Configurer le serveur NFS pour qu'il serve en lecture et écriture (rw) les fichiers du dépôt PXE.

### Noyau iPXE

Le noyau PXE doit être compilé et placé dans le dépot PXE :

```
# Récupération des sources du projet iPXE
git clone git://git.ipxe.org/ipxe.git /tmp/ipxe

# Création du fichier de configuration du boot
touch /tmp/ipxe/src/boot.ipxe
cat  /tmp/ipxe/src/boot.ipxe
#!ipxe
dhcp
chain http://[serveur_tftp]/gpxe-script
EOF

# Compilation du noyeau iPXE
cd /tmp/ipxe/src
make bin/undionly.kpxe EMBED=boot.ipxe
```

*remplacer la variable serveur_tftp par l'adresse IP du serveur TFTP*

Le fichier `bin/undionly.kpxe` doit être copié à la racine du dépôt PXE.

### Script de démarrage iPXE

La séquence de boot de Alpine est ensuite prise en charge par un script nommé `gpxe-script`

```
cat << EOF > /srv/pxe/gpxe-script
#!gpxe
kernel http://[serveur_http]/vmlinuz-vanilla apkovl=http://[serveur_http]/configs/${net0/mac}.tar.gz ip=dhcp ssh_key=http://[serveur_http]/sshkeys.pub modloop=http://[serveur_http]/modloop-vanilla modules=loop,squashfs,sd-mod,usb-storage alpine_dev=nfs:[serveur_nfs]:/srv/pxe alpine_repo=[serveur_apks]
initrd http://[serveur_http]/initramfs-vanilla
boot
EOF
```

*remplacer la variable serveur_http par l'adresse IP du serveur HTTP, la variable serveur_nfs par l'adresse IP du serveur NFS et la variable serveur_apks par l'URL d'accès au dépôt Alpine (DECOS de préférence)*

## Références

Les documentations utiles sont disponibles aux adresses suivantes :

- https://blog.haschek.at/2019/build-your-own-datacenter-with-pxe-and-alpine.html

- https://wiki.debian-fr.xyz/PXE_avec_support_EFI