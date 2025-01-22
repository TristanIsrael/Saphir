# Déboguer les stations blanches

Cette documentation donne des astuces pour le débogage des stations blanches.

## Accéder à une VM depuis le réseau

Pour accéder à une VM, il faut que la VM sys-usb soit démarrée. Celle-ci possède deux interfaces : une sur le réseau local interne et l'autre sur le réseau local externe (connexion physique de l'appareil). L'interface externe doit obtenir son adresse IP grâce à un serveur DHCP.

Pour forcer le démarrage en mode debug, la station blanche doit démarrer avec l'option `Debug=Vrai` sur la ligne de commande du noyau.

Pour ce faire, il y a plusieurs cas de figure.

### Station blanche démarrée par le réseau

### Station blanche nomadisée

### Station blanche démarrée par USB

## Etablir un pont réseau

S'il y a besoin d'accéder au réseau local externe depuis une VM, il faut configurer le pont NAT au sein de la VM sys-net et les routes sur la VM concernée.

Sur la VM sys-net :
```
$ sudo /etc/panoptiscan/scripts/active-routage.sh
```

Sur la VM concernée :
```
$ sudo route add default gw vm-sys-net
```

