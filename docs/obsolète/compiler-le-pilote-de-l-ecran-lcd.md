# Compiler le pilote de l'écran LCD pour le raspi 4

Cette documentation présente les étapes permettant de compiler le pilote pour l'affichage sur l'écran LCD du raspberry Pi 4

## Pré-requis

- Une machine de compilation basée sur une raspberry Pi avec Alpine Standard

## Processus

Taper les commandes suivantes :
```
$ sudo apk add linux-headers raspberrypi-dev
$ cd
$ mkdir build
$ cd build
$ cp [sources]/drivers/rpi-fbcp
$ mkdir rpi-fbcp/build
$ cd rpi-fbcp/build/
$ cmake ..
$ make
```

Copier le fichier fbcp dans le dossier ansible/deploy-infra-pxe/roles/deploy-tftp-server/files


## Installation du driver

https://github.com/alexstacey/MHS35-lcd-64bit-rpi/blob/master/install.sh

Modifier le config.txt et le cmdline.txt
Ajouter le fichier /usr/bin/fbcp
Ajouter le fichier /etc/conf.d/local.start :
```
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

sleep 7
fbcp &

exit 0
```

Créer le fichier /etc/X11/xorg.conf.d/99-fbdev.conf
```
Section "Device"
  Identifier "myfb"
  Driver "fbdev"
  Option "fbdev" "/dev/fb1"
  Option "SwapbuffersWait" "true"
EndSection
```

## Dépendances run

```
$ apk add xf86-video-fbdev
```