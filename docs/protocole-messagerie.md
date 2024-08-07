# Protocole de messagerie et de notification

Ce document définit le protocole de données permettant aux machines virtuelles (`Domaines`) d'échanger des messages à des fins de notification, commande et transfert d'informations. 

## Messagerie, notification, événement

Un message est un document texte au format `JSON`, encodé en UTF-8 et structuré afin de transporter une commande, le résultat d'une action, une notification ou un événement de journal.

## Transport

Les messages sont transportés entre les DomU et le Dom0 au travers du XenBus. Un `pv-channel` spécifique est ouvert entre chaque DomU et le Dom0 pour prendre en charge les messages. Il est accessible via le port série `/dev/hvc1`.

## Structure

Cette section présente la structure de différents types de messages.

Un message type est formaté comme suit :

```
{
    "type": "notification",
    "source": "vm-sys-usb",
    "destination": "tous",
    "payload" :  {
        "categorie": "device",
        "evenement": "connect",
        "chemin": "/mnt/usb_in"
    }
}
```

Cette notification indique que la `vm-sys-usb` a détecté la connexion d'un périphérique USB.

Les valeurs des champs sont les suivantes :

| Champ | Description | Valeurs | Obligatoire |
|----|----|----|----|
| type | Indique le type de message | `notification`, `commande`, `reponse` | Oui |
| source | Indique l'émetteur du message | Nom du domaine ou `dom0` | Oui |
| destination | Indique le domaine destinataire du message | Nom du domaine ou `dom0` ou `tous` | Oui |
| payload | Contient la charge utile propre au `type` de message | chaine JSON | Oui | 

### Notification

Un message dont le `type` est `notification` possède une payload formatée comme suit :

```
{
    "categorie": "device",
    "evenement": "connect",
    "data": {}
}
```

Les valeurs des champs sont les suivantes :

| Champ | Description | Valeurs | Obligatoire |
|----|----|----|----|
| categorie | Indique la catégorie à laquelle appartient la notification | `usb_device` | Oui |
| evenement | Indique le nom de l'événement | `usb_connect`, `usb_disconnect` | Oui |
| data | Fournit des données supplémentaires sur l'événement | | Oui |

### Evénement de journal

TODO

## Bibliothèque

Les messages sont fabriqués grâce à la bibliothèque python `messagerie`. Celle-ci contient plusieurs classes dont :
- `Message` permet de formater un message à envoyer sur le Xenbus
  - `Notification` hérite de `Message` et permet de formater spécifiquement une notification
  - `Commande` hérite de `Message` et permet de formater une commande
  - `Reponse` hérite de `Message` et permet de formater la réponse à une commande

## Spécifications 

Les spécifications techniques des différents messages sont définies dans le document [Commandes du socle](commandes-du-socle.md)