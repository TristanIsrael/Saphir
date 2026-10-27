# ESET

Mise en oeuvre de ESET dans la stations blanche Saphir.

## Notes d'installation en environnement de dev

Pré-requis :
- installer `tar` et `binutils`

Procédure :
- Exécuter le script `./eeau_x86_64.bin`. Les archives d'installation rpm et deb sont décompressées.
- Décompresser l'archive .deb : `ar x eea-11.1.3.0-ubuntu18.x86_64.deb`
- Créer un répertoire `/home/admin/eset`
- Décompresser l'archive data.tar.gz : `tar xvzf data.tar.gz -C /home/admin/eset`

## Notes de test de bon fonctionnement en environnement de dev

Pré-requis :
- `apk add libc6-compat libstdc++ libgcc libcurl` -> NE FONCTIONNE PAS

Installer la glibc :
```
wget -q -O /etc/apk/keys/sgerrand.rsa.pub https://alpine-pkgs.sgerrand.com/sgerrand.rsa.pub
wget https://github.com/sgerrand/alpine-pkg-glibc/releases/download/2.35-r1/glibc-2.35-r1.apk
apk add glibc-2.35-r1.apk
```

## Installation en environnement chroot (Debian)

`apk add debootstrap`
`mkdir -p /var/chroots/debian`
`debootstrap --arch amd64 stable /var/chroots/debian/ https://deb.debian.org/debian`

dans le chroot :
`apt install locales`
