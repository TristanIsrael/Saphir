# Analyse technique

Ce document contient des analyses sur les techiques et technologies à mettre en oeuvre pour atteindre certains objectifs métier.

## Objectifs

Les objectifs suivants doivent être analysés :
- Journalisation d'événements depuis un DomU
- Supervision 
    - Etat des composants logiciels du système (services middleware, API, etc)
    - Etat des composants physiques et métriques (queue IO, CPU, RAM, etc)
- Commandes au Dom0
    - Redémarrage du système
    - Redémarrage d'un DomU
    - Configuration d'une VM (ajout d'un partage P9, etc)
- Commandes fichiers
    - Liste des supports USB connectés
    - Liste des fichiers d'un support
    - Copie de fichier
    - Lecture de fichier
    - Création d'un conteneur chiffré
    - Archivage sécurisé d'un fichier
- Interfaces homme-machine
    - Position de la souris
    - Etat des boutons de la souris
    - Position du toucher tactile
    - Etat des touches du clavier
    - Etat des boutons spéciaux (tablettes tactiles)
    - Clavier virtuel (hors MVP)
- Capteurs physiques
    - Luminosité ambiante
    - Charge de la batterie
    - Etat de l'alimentation secteur
- RPC
    - Echange de messages métier entre DomU
    - Notifications / acquittements entre DomU

## Techniques mises en oeuvre

Les objectifs énumérés peuvent être mis en oeuvre avec les techniques suivantes :

| Objectif                  | Direction     | Catégorie     | Techniques | 
|----|----|----|----|
| Journalisation            | DomU -> DomU  | Messages      | pv channel |
| Supervision logiciels     | Dom0 -> DomU  | Etats         | XenStore  |
|                           | DomU -> DomU  | Etats         | XenStore  |
| Supervision matérielle    | à analyser    |               |  |
| Commandes au Dom0         | DomU -> Dom0  | Messages      | pv channel |
| Commmandes fichiers       | DomU -> DomU  | Messages et 9P| pv channel et 9pfs |
| Interfaces homme-machine  | DomU -> DomU  | Messages      | pv channel |
| Capteurs physiques        | Dom0 -> DomU  | Etats         | XenStore  |
| RPC                       | DomU -> DomU  | Messages      | pv channel |

### XenStore

Le XenStore est une base données à accès contrôlé permettant de créer des enregistrement de type clé-valeur. Elle est accessible à la fois par le Dom0 et les DomU, selon les règles d'accès définies à la configuration (cf `xenstore-chmod`).

Depuis le DomO le XenStore est accessible au travers de la socket Unix `/var/run/xenstored/socket`.
Depuis les DomU il faut passer par le Xenbus `/dev/xen/xenbus`, avec une API du type `pyxs`.

### PV channel

Le PV channel est un canal de données bidirectionnel de pair-à-pair du type série permettant d'échanger des données entre le Dom0 et les DomU ainsi qu'entre les DomU.

La configuration du DomU est faite grâce au paramètre suivant :
```
channel = [ name=nom_du_canal, connection=socket, path=chemin_de_la_socket backend=numero_du_domaine ]
```

Sur le Dom0, le canal est accessible sur la socket Unix définie dans le paramètre `path`.
Sur le DomU, le canal est accessible sur la socket `/dev/hvc[1-9]`. Le canal `0` est réservé à la console du DomU, le premier canal auxiliaire créé aura l'identifiant `hvc1`.

Le paramètre `backend` peut être utilisé pour créer un canal avec un DomU directement.

### 9pfs

Le protocole Plan9 est pris en charge par Xen grâce au protocole 9p et au driver backend/frontend utilisant le XenBus pour réaliser des montages de systèmes de fichiers distants, sur le Dom0 ou un DomU.

La configuration du DomU est grâce au paramétrage suivant :
```
p9 = [
	"tag=nom_du_tag_P9, path=chemin_du_partage, backend=_numero_du_domaine, security_model=none"
]
```

Dans le DomU, le montage est réalisé grâce à la commande suivante :
```
# mount -t 9p -o trans=xen,version=9p2000.L nom_du_tag_P9 chemin_du_point_de_montage
```

### Surveillance des supports USB

L'implémentation de 9pfs de Xen ne gère pas les notifications en cas de changement sur les inodes ou sur le système de fichier.

Il est donc nécessaire d'utiliser une technique de polling pour surveiller les fichiers et répertoires du disque.

```
import logging
from watchdog.observers.polling import PollingObserver
from watchdog.events import LoggingEventHandler

logging.basicConfig(level=logging.INFO)
event_handler = LoggingEventHandler()
observer = PollingObserver()
observer.schedule(event_handler, "/chemin/du/dossier", recursive=False)
observer.start()
observer.join()
```

### Stratégie

La stratégie de gestion des supports USB est expliquée dans cette section.

#### Stratégie nominale

Les supports USB sont gérés par le domaine `vm-sys-usb`. 
Ce domaine expose sur le Xenbus avec le driver 9P les répertoires suivants :
- `/mnt/usb/`

Lorsqu'un support USB est connecté, un nouveau point de montage apparaitra dans `/mnt/usb`. Chaque point de montage est préfixé avec un ordre séquentiel d'apparition sur le système :
- `/mnt/usb/1-Maclé`
- `/mnt/usb/2-NO NAME`

Les domaines qui souhaitent accéder directement aux fichiers peuvent créer un lien `9p` avec le domaine `vm-sys-usb` et accéder au contenu du ou des disques montés en tant que sous-répertoire du point de montage `/mnt/usb`.

#### Stratégie dégradée

Les tests actuels montrent un dysfonctionnement lors de l'établissement d'un lien 9P direct entre deux domaines utilisateurs (DomU).

*Aucune stratégie dégradée n'a été identifiée pour l'heure.*

### Cardinalités avec vm-sys-usb

Le domaine `vm-sys-usb` n'est pas visibile de tous les domaines pour des raisons de sécurité. Exposer les fichiers contenus sur un support USB vers d'autres domaines les expose à des risques d'infection.
En conséquence, tous les domaines qui sont connectés directement via le partage 9pfs avec le domaine `vm-sys-usb` sont considérés comme à *risque*.

Afin d'éviter que les domaines métier non techniques (par exemeple le contrôleur ou la GUI) ne soient considérés comme des domaines à risque, un protocole spécifique est mis en oeuvre, permettant entre autres le listing des fichiers d'un support USB ou la copie de fichiers. Ce protocole utilise les mécanismes de la messagerie DomU->Dom0.

## Débogage

### Débogage des sockets pv channel

Côté Dom0 : `# socat UNIX-CONNECT:chemin_de_la_socket -`
Côté DomU : `# tail -f /dev/hvc1` pour lire et `echo "TEST" > /dev/hvc1` pour écrire *(obsolète) `printf du_texte | socat UNIX-CONNECT:/dev/hvc1 -` pour écrire*

## Souris et écran tactile

L'objectif est de détecter automatiquement la souris et l'écran tactile sur le système pour les surveiller et exporter leurs états dans le XenStore.

## Versions de noyaux

Les versions des noyaux utilisées par le Dom0 et les DomU doivent être cohérentes.

### Extraction des modules 

Pour extraire les modules du fichier `modloop`, utiliser la commande suivante :
`unsquashfs modloop`

Pour extraire les fichiers initramfs :
`zcat initramfs | cpio -idm`

### Synchronisation Dom0 et DomU

Les objectifs sont :
- avoir des versions de noyaux identiques entre Dom0 et DomU
- avoir des versions de modules correspondant aux noyaux
- éviter les copies de fichiers modules sur les DomU (limiter l'empreinte mémoire)

Pour atteindre ces objectifs, l'organisation est la suivante :
- posséder la dernière version du paquet `linux-lts` sur le Dom0.
- télécharger la dernière version du paquet `linux-virt` sur le Dom0.
  - décompresser le paquet `linux-virt`
  - mettre à disposition le noyau `vmlinuz-virt` pour les DomU
  - créer un modloop `modloop-virt` avec les fichiers du paquet `linux-virt` (`mksquashfs ./lib/modules modloop-virt`)
  - mettre à disposition le fichier `modloop-virt` pour les DomU
  - décompresser le fichier `initramfs-virt`
    - supprimer les fichiers `/var/lib/modules/*`
    - copier les fichiers `/var/lib/modules/6.6.*` du modloop-virt dans l'initramfs
    - recompresser le fichier `initramfs-virt` avec la commande `find . -print0 | cpio --null -ov --format=newc > initramfs-virt & gzip ./initramfs-virt & mv initramfs-virt.gz initramfs-virt`

### Mise à disposition des modules pour les DomU

Les modules sont fournis grâce à la valeur `modloop=modloop-virt` du paramètre `extra` pour chaque DomU. Cela a pour conséquence de monter le fichier `/boot/modloop-virt` au démarrage du DomU.

Il faut préparer un fichier modloop minimal adapté à chaque type de DomU pour optimiser l'utilisation de la RAM.

```
# mkdir /tmp/modloop
# cp -r /lib/modules /tmp/modloop
# cd /tmp/modloop
# mksquashfs . /boot/modloop-virt
```

La commande `unsquashfs -l /boot/modloop-virt` doit afficher ceci :
```
...
squashfs-root/modules/6.6.14-0-virt/kernel/sound/pci/hda/snd-hda-codec.ko
squashfs-root/modules/6.6.14-0-virt/kernel/sound/pci/hda/snd-hda-intel.ko
squashfs-root/modules/6.6.14-0-virt/kernel/sound/virtio
squashfs-root/modules/6.6.14-0-virt/kernel/sound/virtio/virtio_snd.ko
squashfs-root/modules/6.6.14-0-virt/kernel/virt
squashfs-root/modules/6.6.14-0-virt/kernel/virt/lib
squashfs-root/modules/6.6.14-0-virt/kernel/virt/lib/irqbypass.ko
squashfs-root/modules/6.6.14-0-virt/kernel-suffix
...
```

Autre possibilité : injecter les modules directement dans l'initramfs

```
# mkdir /tmp/initramfs-lts
# cd /tmp/initramfs-lts
# cp /boot/initramfs-lts .
# zcat initramfs-lts | cpio -idm
# cp /lib/modules/[version]/... lib/modules/[version]/...
# rm initramfs-lts
# find . -print0 | cpio --null -ov --format=newc > initramfs-lts
# gzip /boot/initramfs-lts
# mv /boot/initramfs-lts.gz /boot/initramfs-lts
```

### Modules utilisés par les DomU

X ipv6                  716800  14
X simpledrm              16384  0
X drm_shmem_helper       28672  1 simpledrm
X drm_kms_helper        266240  1 simpledrm
X syscopyarea            12288  1 drm_kms_helper
X sysfillrect            12288  1 drm_kms_helper
X sysimgblt              12288  1 drm_kms_helper
X fb_sys_fops            12288  1 drm_kms_helper
X drm                   774144  3 drm_kms_helper,drm_shmem_helper,simpledrm
X i2c_core              126976  2 drm_kms_helper,drm
X drm_panel_orientation_quirks    24576  1 drm
X fb                    135168  1 drm_kms_helper
X fbdev                  12288  1 fb
ext4,crc16,crc32c_generic,mbcache,jbd2,squashfs,loop,9p,9pnet,9pnet_xen,netfs,fscache

## PCI passthru

```
# echo 0000:00:04.0 > /sys/bus/pci/devices/0000:00:04.0/driver/unbind
# echo 0000:00:04.0 > /sys/bus/pci/drivers/pciback/new_slot
# echo 0000:00:04.0 > /sys/bus/pci/drivers/pciback/bind
# xl pci-assignable-add "00:04.0"
```

### Udev

Les supports USB sont détectés automatiquement par udev/mdev sur la VM `vm-sys-usb`. udev détecte l'ajout du périphérique et recherche une règle compatible dans le dossier `/etc/udev/rules.d`.
Dans ce dossier doit être placé le fichier `99-usbdisk.rules` appartenenant au projet.

Ce fichier contient les règles suivantes :
`ENV{ID_FS_USAGE}=="filesystem|other|crypto", ENV{ID_FS_LABEL_ENC}=="?*", RUN+="/usr/local/panoptiscan/scripts/mdev-usb-storage"`

### Notes

Pour recharger les règles de udev : `udevadm control --reload-rules`
Pour exécuter les règles : `udevadm trigger`
Pour vérifier que udev a détecté un périphérique : `udevadm info --name /dev/sda1 --query all`
Pour tester l'exécution des règles : `udevadm test /dev/sda1`
Pour observer les règles : `udevadm monitor`

Environnement lors de la connexion d'une clé USB :
```
ID_BUS=usb
DEVNAME=/dev/sda1
ACTION=add
SHLVL=1
ID_SERIAL_SHORT=1-0000:00:03.0-4.1
SEQNUM=3229
USEC_INITIALIZED=4374446177
ID_PART_ENTRY_SIZE=16777184
ID_USB_DRIVER=usb-storage
ID_FS_UUID_ENC=6f5209d3-5e99-4a33-b531-6c52b4e4f5ef
ID_TYPE=disk
MAJOR=8
ID_FS_LABEL_ENC=Transfert
ID_INSTANCE=0:0
DEVPATH=/devices/pci-0/pci0000:00/0000:00:00.0/usb1/1-4/1-4.1/1-4.1:1.0/host0/target0:0:0/0:0:0:0/block/sda/sda1
ID_FS_UUID=6f5209d3-5e99-4a33-b531-6c52b4e4f5ef
ID_PART_TABLE_TYPE=dos
ID_PART_ENTRY_SCHEME=dos
ID_FS_LABEL=Transfert
ID_MODEL_ENC=QEMU\x20HARDDISK\x20\x20\x20
ID_PART_ENTRY_TYPE=0x83
ID_USB_INTERFACES=:080650:
ID_FS_VERSION=1.0
ID_MODEL=QEMU_HARDDISK
DEVLINKS=/dev/disk/by-id/usb-QEMU_QEMU_HARDDISK_1-0000:00:03.0-4.1-0:0-part1 /dev/disk/by-label/Transfert /dev/disk/by-path/xen-pci-0-pci-0000:00:00.0-usb-0:4.1:1.0-scsi-0:0:0:0-part1 /dev/disk/by-uuid/6f5209d3-5e99-4a33-b531-6c52b4e4f5ef
ID_SERIAL=QEMU_QEMU_HARDDISK_1-0000:00:03.0-4.1-0:0
SUBSYSTEM=block
ID_MODEL_ID=0001
DISKSEQ=16
MINOR=1
ID_FS_TYPE=ext4
ID_PATH=xen-pci-0-pci-0000:00:00.0-usb-0:4.1:1.0-scsi-0:0:0:0
ID_VENDOR_ENC=QEMU\x20\x20\x20\x20
ID_PATH_TAG=xen-pci-0-pci-0000_00_00_0-usb-0_4_1_1_0-scsi-0_0_0_0
PARTN=1
ID_PART_ENTRY_DISK=8:0
ID_PART_ENTRY_OFFSET=32
ID_VENDOR=QEMU
PWD=/
DEVTYPE=partition
ID_PART_ENTRY_NUMBER=1
ID_USB_INTERFACE_NUM=00
ID_VENDOR_ID=46f4
ID_FS_USAGE=filesystem
ID_REVISION=2.5+
```

Le libellé du disque est contenu dans la variable `ID_FS_LABEL_ENC` et le système de fichier dans la variable `ID_FS_TYPE`.

Contenu du fichier mdev-usb-storage :
```
#!/bin/sh

LIBELLE=$ID_FS_LABEL_ENC
FS=$ID_FS_TYPE
POINT_MONTAGE=/media/usb/$LIBELLE
PERIPHERIQUE=$DEVNAME
JOURNAL=/var/log/panoptiscan/udev.log

echo "Action : $ACTION" >> /var/log/panoptiscan/udev.log

if [ "$ACTION" == "add" ]
then
        echo "Montage de la partition $LIBELLE avec le systeme de fichier $FS dans $POINT_MONTAGE" >> $JOURNAL
        echo mount $PERIPHERIQUE $POINT_MONTAGE >> $JOURNAL
        mkdir -p $POINT_MONTAGE
        mount $PERIPHERIQUE $POINT_MONTAGE

        echo "Envoi de la notification aux DomU" >> $JOURNAL

fi

if [ "$ACTION" == "remove" ]
then
        echo "Demontage de $POINT_MONTAGE" >> $JOURNAL
        umount $POINT_MONTAGE
        rmdir $POINT_MONTAGE

        echo "Envoi de la notification aux DomU" >> $JOURNAL
fi
```

# IOMMU

Ajouter `iommu=soft` si le matériel ne supporte pas l'IOMMU.
Il faut utiliser de préférence IOMMU (VT-d sous Intel) et HVM pour plus de sécurité.
Pour rendre l'utilisation de l'IOMMU obligatoire (ne pas booter si l'IOMMU n'est pas disponible ou activé), utiliser `iommu=required`.

Pour vérifier si l'IOMMU est activé sur l'hôte : `dmesg | grep -e DMAR -e IOMMU`

# GRUB et UEFI

S'il manque l'entrée Xen dans le menu Grub, il faut renommer le fichier /boot/vmlinuz-lts pour que son nom coincide avec celui de config*.

# Machine virtuelle QEMU

Si le système est utilisé au sein d'une machine virtuelle fournie par QEMU, il faut qu'elle prenne en charge l'IOMMU et VT-d.

Il faut donc que la ligne de commande de qemu contienne les éléments suivants :
```
-cpu ..., +vmx
-device intel-iommu
```

# Bug Grub sur Alpine 3.20

Après l'installation de XEN grub n'affiche pas d'entrée pour Xen. Il faut créer un lien symbolique de `/boot/vmlinuz-lts` vers `/boot/vmlinuz-6.6.32-0-lts`.

# Problème de boot sur la tablette Getax UX10

Le noyau XEN démarre mais au moment de booter le dom0 la machine redémarre.
La solution est de reprendre la configuration Grub de la clé USB d'installation :
- insérer la clé USB d'installation
- monter la partition boot dans `/media/usb`
- sauvegarder le fichier `/boot/grub/grub.cfg`
- copier le fichier `/media/usb/boot/grub/grub.cfg` dans `/boot/grub`
- éditer le fichier `/boot/grub/grub.cfg` et ajouter les paramètres `root` et `rootfstype` avec les valeurs contenues dans le fichier `/boot/grub/grub.cfg` initial.
- ne pas exécuter `update-grub`
- redémarrer.

# Performances

## Partage de fichiers entre VM (dépôt)

Dans l'idéal, les fichiers sont accessibles depuis n'importe quelle VM directement sur le support USB connecté sur `sys-usb`. Or à l'heure actuelle, le partage de fichiers entre VM ne fonctionne pas (problème de configuration ?).

La stratégie actuellement mise en oeuvre consiste à copier le fichier dans un dépôt local avant de l'analyser.
Les avantages et inconvénients sont les suivants :
- (+) les fichiers de la clé ne peuvent pas être modifiés accidentellement par un processus métier
- (-) la copie du fichier dans le dépôt induit une latence dans le processus
  - *ce point doit faire l'objet d'une analyse comparative pour mesurer la latence*
- (-) la copie du fichier dans le dépôt diminue la RAM disponible.
- (-) le partage 9P ne permet pas de protéger les fichiers contre les modifications ni contre la corruption.

Le dépôt doit :
- permettre de partager des fichiers entre machines virtuelles.
- être rapide.
- protéger les fichiers contre les modifications et la corruption, une fois le fichier écrit il ne doit plus être modifié.

Pour améliorer les performances, une piste consiste à remplacer le partage de fichier 9P actuel par un partage de fichier du type disque. Pour ce faire, créer un fichier `raw` sur le dom0 et l'ajouter dans la configuration des VM :
`disk = [ 'file:/chemin/du/fichier.raw,xvda,w!' ]`. L'utilisation du `!` est critique pour permettre un partage du fichier entre VM.

Avantages et inconvénients :
- (+) Le Dom0 n'a plus la possibilité d'accéder directement aux fichiers, ce qui réduit la surface d'attaque.

**La gestion de la concurrence est à la charge du sous-système métier**. *Voir si le socle peut proposer des mécanismes, notamment en fournissant des notifications*.

## GPU Intel HDU Graphics (iGPU)

pris en charge par le module i915 mais avec un problème à GVT-d : https://events.static.linuxfound.org/sites/events/files/slides/XenGT-Xen%20Summit-REWRITE%203RD%20v4.pdf

- https://blog.tmm.cx/2020/05/15/passing-an-intel-gpu-to-a-linux-kvm-virtual-machine/
- https://github.com/intel/gvt-linux/wiki/GVTg_Setup_Guide 

Les modules suivants doivent être disponibles sur le Dom0 : `kvmgt`, `i915`, `vfio`, `mdev`, `kvm`, `drm`, `drm_kms_helper`, `video`, `drm_display_helper`, `ttm`, `intel-gtt`, `hwmon`, `drm_buddy`, `cec`, `i2c-algo-bit`.

Résumé : 
- Configurer la ligne de commande du noyau
- Charger les modules `kvmgt`, `vfio-iommu-type1`, `vfio-mdev`.
- Créer un GPU virtuel.
- ...

**Si l'une des étapes ne fonctionne pas, il est peut-être nécessaire de compiler les modules manquants. Cf sections suivantes.**

### Configuration du noyau

Editer le fichier `/etc/default/grub` et ajouter les options suivantes à la fin de la ligne `GRUB_CMDLINE_LINUX_DEFAULT` :
```
i915.enable_gvt=1 i915.enable_fbc=0
```

*Note : l'option `intel_iommu=1` doit rester présente*

Exécuter la commande `$ sudo update-grub`.

### Chargement automatique des modules

Editer le fichier `/etc/modules-load.d/gvt.conf` avec le contenu suivant :
```
kvmgt
vfio-iommu-type1
vfio-mdev
```

### Création d'un GPU virtuel

Vérifier la présence du répertoire `/sys/bus/pci/devices/0000:00:02.0/mdev_supported_types`.
En cas d'absence, vérifier les options du noyau et redémarrer.

Générer un UUID avec la commande `$ uuidgen`. Exemple : `255a5189-28b0-4ae5-81e8-782f33891d97`.

Créer un GPU virtuel avec la commande `echo (uuid) | sudo tee mdev_supported_types/i915-GVTg_V5_8/create`. *Note : Remplacer (uuid) par l'UUID généré par la précédente commande*.

### Compilation du module kvmgt (si nécessaire)

```
$ git clone https://github.com/alpinelinux/aports.git
$ cd aports
$ git switch 3.19-stable
$ abuild checksum
$ abuild deps
$ abuild unpack
$ abuild prepare
$ abuild build
```

Laisser se dérouler la compilation du noyau (pendant plusieurs heures)/

Modifier le fichier `src/build-lts.x86_64/.config` :
```
CONFIG_DRM_I915_GVT_KVMGT=m
```

Poursuivre avec :

```
$ cd src/build-lts.x86_64
$ make modules
$ sudo cp -r /var/lib/modules/6.6.32-0-lts /var/lib/modules/6.6.32-0-lts.orig
$ sudo make modules_install
$ sudo depmod -a
```

Le noyau est disponible à l'emplacement `src/build-lts.x86_64/arch/x86/boot/bzImage`.
En cas de remplacement du noyau, taper la commande `$ sudo cp src/build-lts.x86_64/arch/x86/boot/bzImage /boot/vmlinuz-6.6.32-0-lts`. Modifie le fichier `grub.cfg` en conséquence.

### Mise à jour de l'initramfs

```
$ sudo cp /boot/initramfs-lts /boot/initramfs-lts.orig
$ sudo mkinitfs -c /etc/mkinitfs/mkinitfs.conf 6.6.32-0-lts
```

Mettre à jour le fichier `grub.cfg` en conséquence.

## Affichage

Sur tablette, il peut être nécessaire de faire pivoter l'affichage. Pour ce faire, ajouter `fbcon=rotate:1` sur la ligne de commande grub.