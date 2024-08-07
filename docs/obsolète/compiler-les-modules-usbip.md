# Compiler les modules de noyau USB IP

Cette documentation explique comment compiler les modules USB IP pour le noyau des machines virtuelles de la station blanche.

## Pré-requis

- Télécharger aports : 
```
$ cd 
$ git clone https://...
```

- Machine virtuelle de build

## Procédure

Taper les commandes suivantes (**sur une machine connectée à Internet**) :

```
$ cd /home/admin/aports/main/linux-lts
$ abuild checksum
$ cd src/build-virt.x86_64
$ make scripts prepare modules_prepare
$ make modules
```

Les modules sont dans le répertoire /home/admin/aports/main/linux-lts/src/build-virt.x86_64/drivers/usb/usbip/*.ko
