# Références

## Internet

### Général

https://documentation.suse.com/es-es/sles/15-SP3/html/SLES-all/book-virtualization.html 
https://wiki.xenproject.org/wiki/Xen_Project_4.9_Man_Pages
https://theswissbay.ch/pdf/Books/Computer%20science/The%20Definitive%20Guide%20to%20the%20Xen%20Hypervisor%20-%20David%20Chisnall.pdf 

### Performance

https://www.starlab.io/blog/benchmarking-xen-virtualization

### Xen ARM

https://developer.nordicsemi.com/nRF_Connect_SDK/doc/v1.6-branch/zephyr/boards/arm64/xenvm/doc/index.html

### Communications

https://www.quora.com/How-do-you-realize-the-communication-between-Dom0-and-Domu-in-Xen 
https://xenbits.xen.org/docs/4.6-testing/misc/console.txt
https://dl.ifip.org/db/conf/middleware/middleware2007/ZhangMRG07.pdf 
https://www.informit.com/articles/article.aspx?p=1187966&seqNum=7

### Configuration

https://xenbits.xen.org/docs/unstable/man/xl.cfg.5.html

### Commandes XEN

https://wiki.xenproject.org/wiki/XenStore

### Programmation python

https://github.com/selectel/pyxs
http://pyxs.readthedocs.org/en/latest/

## Créer un PV channel data 

Par défaut une VM est associée à un PV channel de console `/local/domain/[vmid]/console` qui sert à échanger des données de type `texte` entre le domU et le dom0.

## Commandes xen

| Commande | Description |
|-------|--------|
| `xenstore-list /local/domain/[vmid]` | Affiche la liste des clés du Xen store pour la VM |
| `xenstore-list -f` | Affiche toutes les clés et valeurs des domaines |
| `xenstore-read /local/domain/[vmid]/[cle]` | Affiche la valeur pour une clé spécifique d'une VM |

## Tests pyxs

```
python3 -m venv /usr/local/panoptiscan
. /usr/local/panoptiscan/bin/activate
pip install pyxs

...

deactivate
```

## Xenbus vs Unix socket

**On ne peut pas surveiller les événements sur une clé en passant par le XenBus, il faut utiliser une socket (`/var/run/xenstored/socket`)**, hors ce mécanisme n'est possible que sur le Dom0. Sur les DomU il faut passer par le XenBus (`/dev/xen/xenbus`).

## 9pfs

Paquet nécessaire : xen-qemu

Config XEN : `p9=["tag=partage,path=/var/lib/xen/partage,backend=0,security_model=none"]`
Montage sur DomU : `mount -t 9p -o trans=xen,version=9p2000.L partage /media/partage`

## VGA passthru

https://mathiashueber.com/windows-virtual-machine-gpu-passthrough-ubuntu/