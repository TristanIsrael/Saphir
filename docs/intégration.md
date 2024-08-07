# Notes d'intégration

## Dom0

Les modules xen-pciback, xen-netback et xen-blkback doivent être chargés.
> Les modules doivent être ajoutés au fichier /etc/modules
> Le script /etc/init.d/modules doit être chargé automatiquement (`rc-update add modules default`).

Après qu'une VM a démarré il faut lui assigner les ports PCI qui la concernent.
> Le chargement de la VM et l'assignation des ports PCI doivent être faits via un script unique.

## Dell Latitude E5510

La configuration matérielle de cette platforme oblige à faire fonctionner le système en mode dégradé :
- PCI passthru remplacé par VGA passthru pour la carte graphique.

### Firmware

Le firmware doit être configuré en BIOS legacy.

### Bootloader

Le système doit être démarré avec les paramètres suivants sur la ligne de commande du kernel :
`intel_iommu=on iommu=soft`.

### vm-controleur

Pour faire fonctionner la VM contrôleur il faut utiliser le **VGA passthru** :

```
gfx_passthru=1
pci = ['00:02.0']
```

En mode **HVM** avec les paramètres `kernel`, `ramdisk` et `extra` le driver `i915` doit être utilisé à l'intérieur du DomU. Un firmware n'a pas besoin d'être spécifié, `seabios` sera utilisé automatiquement.
Le framebuffer `/dev/fb1` doit être utilisé.
Un bootloader doit être installé :
```
# apk add syslinux
# extlinux -i /boot
```

Note : Le démarrage est assez long (environ 40 secondes).

En mode **PV** il ne semble pas possible de démarrer le DomU.

Pour démarrer l'application Qt il faut utiliser la commande `$ python3 main.py -platform linuxfb:fb=/dev/fb1`

### sys-usb

Les bus USB sont rattachés aux périphériques PCI `00:1a.0` et `00:1d.0`.

Le PCI passthru sur ces périphériques est interdit par le BIOS : 
```
(XEN) [VT-D] It's disallowed to assign 0000:00:1a.0 with shared RMRR at db7d7000 for d10.
(XEN) d10: assign (0000:00:1a.0) failed (-1)
(XEN) [VT-D] It's disallowed to assign 0000:00:1d.0 with shared RMRR at db7d7000 for d10.
(XEN) d10: assign (0000:00:1d.0) failed (-1)
```

Pour régler ce problème il faut ajouter `,rdm_policy=relaxed` à la définition PCI pour chaque port :
`pci = ['00:1d.0,rdm_policy=relaxed', '00:1a.0,rdm_policy=relaxed']`.

Mettre le DomU en mode `PV`.

## GETAC UX10 G2

La tablette UX10 comporte un écran de 10 pouces avec une surface tactile, un disque NVME, un processeur Core i5 doté de 8 coeurs et une puce graphique intégrée (au Core i5) UHD Graphics.

### Performances

Bogomips =

### Problématique

La GETAC UX10 embarque un GPU Intel UHD dont l'utilisation en passthru est complexe, même en VGA passhtru. Le modèle utilisé pour les tests ne permet pas de passer en mode BIOS faute de mot de passe administrateur.

La mise en oeuvre du système avec ce type de GPU oblige à utiliser les fonctionnalités GVT (voir références).

### Références 
- https://github.com/intel/gvt-linux/wiki/GVTg_Setup_Guide

La configuration matérielle de cette platforme oblige à faire fonctionner le système en mode dégradé :

### Firmware

Le système sous test est bloqué en mode UEFI.

### Bootloader

Voir Dell Latitude E5510

### vm-controleur

Voir Dell Latitude E5510

## GETAC T800 G2

La tablette T800 comporte un écran de 8 pouces avec une surface tactile, un disque NVME, un processeur Atom x7 doté de 4 coeurs tournant à 1,6 Ghz et d'une puce graphique (intégrée au CPU) Intel HD Graphics.

Bogomips = 3200