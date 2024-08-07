# Créer l'infrastructure de déploiement

Cette documentation indique comment mettre en oeuvre l'indrastructure de déploiement. 

L'infrastructure de déploiement PXE s'appuie sur les services suivants :

| Nom          | Adresse IPv4     | Description |
|--------------|------------------|-------------------------------|
| DHCP | 192.168.10.1 | Serveur DHCP pour le boot PXE |
| TFTP | 192.168.10.1 | Serveur TFTP pour le boot PXE |
| HTTP | 192.168.10.2 | Serveur HTTP servant les configurations des stations blanches |
| NFS | 192.168.10.2 | Serveur NFS permettant à l'intégrateur de stocker ou modifier les configurations des stations blanches |
| DEPOTS | 192.168.10.3 | Serveur HTTP servant les paquets Alpine (APK) |
| ADMIN | 192.168.10.250 | Machine permettant à l'administrateur d'installer et de configurer l'infrastructure de déploiement |

## Etapes

La création de l'infrastructure se fait en deux étapes :

1. Création des machines virtuelles

2. Déploiement et configuration des services

## Pré-requis

L'administrateur doit avoir à sa disposition :

- le kit d'installation dans lequel figure cette documentation

- la dernière version de l'ISO Alpine extended

- la dernière version de l'image ISO Alpine XEN

- la dernière version de l'image ISO Alpine Virtual

- un miroir du dépôt officiel des paquets Alpine (voir *Créer un miroir des dépôts Alpine*)

## Création des machines virtuelles

Cette section décrit les étapes de création des machines virtuelles de l'infrastructure. Les machines doivent être créées dans l'ordre indiqué.

### Poste d'administration

Cette section décrit la création d'une machine pour l'administrateur.

*à compléter*

### Dépôts embarqués

Les dépôts Alpine peuvent être stockés sur un serveur HTTP existants s'il en existe un dans le réseau. Cette section indique comment créer un nouveau serveur HTTP pour les dépôts Alpine.

**La machine doit avoir au moins 2Go de mémoire.**

- Démarrer sur la machine avec l'ISO Alpine standard.

- A l'invite de login, taper `root` puis Entrée. L'authentification est terminée.

- Taper la commande `setup-keymap`. Taper ensuite `fr`, puis Entrée, puis `fr`, puis Entrée. Le clavier est à présent en français.

- Taper la commande `setup-interfaces`

- A la question `Which one do you want to initialize?`, taper `eth0` puis Entrée

- A la question `Ip address fot eth0?`, taper `192.168.10.3` puis Entrée

- A la question `Netmask?`, taper `255.255.255.0` puis Entrée

- A la question `Gateway?`, taper `none` puis Entrée

- A la question `Do you want to do any manual network configuration?`, taper `n` puis Entrée

- Taper la commande `/etc/init.d/networking restart`. Le serveur est à présent configuré avec l'adresse IP `192.168.10.3`

- Taper la commande `rc-update add networking`

- Taper la commande `setup-sshd` puis Entrée.

- A la question `Which SSH server`, taper `openssh` puis Entrée

- Le serveur SSH est à présent configuré

- Taper la commande `adduser admin` puis Entrée. Ssaisissez ensuite un mot de passe fort puis Entrée (deux fois consécutives)

- Taper les commandes suivantes :
```
mkdir -p /var/depots/alpine/main/x86_64
chown -R admin:admin /var/depots/main/x86_64
chmod -R 770 /var/depots/main/x86_64
```

- Depuis une machine d'administration connectée au même réseau, décompresser l'archive alpine.tar contenant les fichiers du dépôt Alpine dans le dossier `/tmp/alpine`, et taper les commandes suivantes : 
```
scp /tmp/alpine/main/x86_64/dosfstools-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/grub-efi-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/sfdisk-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/lddtree-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/xz-libs-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/zstd-libs-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/kmod-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/argon2-libs-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/device-mapper-libs-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/json-c-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/cryptsetup-libs-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/mkinitfs-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/grub-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/libfdisk-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
scp /tmp/alpine/main/x86_64/libsmartcols-*.apk admin@192.168.10.3:/var/depots/alpine/main/x86_64
linux-lts*
linux-firmware*
openssh*
ncurses*
libedit*
busybox*
```

- Modifier le fichier `/etc/apk/repositories` et y insérer la ligne `/var/depots/alpine/main`

- Taper la commande `apk update` puis Entrée.

- Taper la commande `setup-disk` puis Entrée.

- A la question `Which disk(s) do you like to use?`, taper `sda` puis Entrée

- A la question `How would you like to use it?`, taper `sys` puis Entrée

- A la question `WARNING: Erase the above disk(s) and continue?`, taper `y` puis Entrée

- A la fin de l'installation, taper `reboot`

- A l'invite de login, taper `root` puis Entrée. L'authentification est terminée.

- Taper la commande `setup-hostname` puis Entrée, puis `depots.local`, puis Entrée

- Taper la commande `passwd` puis Entrée. Saisissez un mot de passe fort pour le compte root (à deux reprises).

- Taper les commandes suivantes :
```
mkdir -p /var/depots/alpine/
chown -R admin:admin /var/depots/
chmod -R 770 /var/depots/
```

- Depuis la machine d'administration, taper les commandes suivantes 
```
cd [répertoire des fichiers alpine contenant le dossier main et le dossier community]
scp -r main community admin@192.168.10.3:/var/depots/alpine
```

- Modifier le fichier `/etc/apk/repositories` et y insérer les lignes suivantes :
```
/var/depots/alpine/main
/var/depots/alpine/community
```

- Taper la commande `apk update` puis Entrée.

- Taper la commande `setup-timezone` puis Entrée, puis `Europe/Paris`, puis Entrée

- Taper les commandes suivantes :
```
apk add lighttpd
rc-update add lighttpd default
```

- Editer le fichier `/etc/lighttpd/lighttpd.conf` et ajouter à la fin du fichier `server.dir-listing = "enable"`

### Dépôts sur un stockage réseau (CIFS)

Dans le cas où le mirroir du dépôt est sur un stockage réseau accessible via CIFS (partage de fichier Windows), cette machine virtuelle servira uniquement d'intermédiaire. La configuration peut être réalisée comme suit.

**Résumé de la configuration :**
La machine virtuelle sera configurée comme un serveur réseau normal avec un nom d'hôte. 512 Mo de RAM sont suffisants.

- Démarrer sur la machine avec l'ISO Alpine standard.

- A l'invite de login, taper `root` puis Entrée. L'authentification est terminée.

- Taper la commande `setup-keymap`. Taper ensuite `fr`, puis Entrée, puis `fr`, puis Entrée. Le clavier est à présent en français.

- Taper la commande `setup-interfaces`

- A la question `Which one do you want to initialize?`, taper `eth0` puis Entrée

- A la question `Ip address for eth0?`, taper `dhcp` puis Entrée.

- A la question `Do you want to do any manual network configuration?`, taper `n` puis Entrée

- Taper la commande `/etc/init.d/networking restart`. Le serveur est à présent configuré avec l'adresse IP fournie par le serveur DHCP.

- Taper la commande `rc-update add networking`

- Taper la commande `setup-sshd` puis Entrée.

- A la question `Which SSH server`, taper `openssh` puis Entrée

- Le serveur SSH est à présent configuré

- Taper la commande `adduser admin` puis Entrée. Ssaisissez ensuite un mot de passe fort puis Entrée (deux fois consécutives)

A COMPLETER

### Serveur DHCP

Le serveur DHCP doit être installé à partir d'une ISO de Alpine Linux standard 3.15 minimum.

- Démarrer sur la machine avec l'ISO Alpine standard.

- A l'invite de login, taper `root` puis Entrée. L'authentification est terminée.

- Taper la commande `setup-alpine` puis Entrée.

- à compléter

Suivez ensuite les instructions de la section *Configuration commune*.

### Serveur HTTP/TFTP/NFS

Le serveur HTTP/TFP/NFS doit être installé à partir d'une ISO de Alpine Linux standard 3.15 minimum.

- Démarrer sur la machine avec l'ISO Alpine standard.

- A l'invite de login, taper `root` puis Entrée. L'authentification est terminée.

- Taper la commande `setup-alpine` puis Entrée.

- à compléter

Suivez ensuite les instructions de la section *Configuration commune*.

### Configuration commune

Chaque machine doit être configurée avec un utilisateur permettant de déployer les services grâce à Ansible.

- Taper la commande `adduser ansible` puis Entrée. Saisir un mot de passe fort pour l'utilisateur (deux foix consécutives).

- Ajouter les lignes suivantes dans le fichier /etc/apk/repositories :
```
http://192.168.10.3/alpine/main
http://192.168.10.3/alpine/community
```

- Taper la commande `visudo` puis Entrée.

## Déploiement des services

à rédiger