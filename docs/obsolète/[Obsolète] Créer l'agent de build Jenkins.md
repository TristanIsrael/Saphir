# Créer l'agent de build Jenkins

Cette documentation explique comment créer l'agent qui va permettre de builder les paquets APK Alpine avec Jenkins

## Etapes

- Créer une machine virtuelle avec 1 Go de RAM et 2 Go de disque

- \# sudo apk add avahi-daemon dbus alpine-sdk

- \# sudo adduser admin

- Taper la commande \# visudo et décommenter la ligne \#%wheel ALL=(ALL) NOPASSWD: ALL

- Se logger en tant qu'utilisateur admin

- $ sudo mkdir -p /var/cache/distfiles

- $ sudo chmod a+w /var/cache/distfiles