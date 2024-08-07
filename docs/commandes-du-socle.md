# Commandes du socle

Le socle prend en charge un certain nombre de fonctionnalités et assure leur bonne exécution, leur sécurité et leur sûreté.

Ce document énumère et décrit chaque fonction au travers des messages et notifications qui permettent de les mettre en oeuvre.

## Résumé

Dans les chapitres suivants, la convention suivante s'applique :
- *DomU* désigne un domaine utilisateur du segment métier.
- *Tous* désigne l'ensemble des domaines des segments socle et métier, y compris le Dom0.

### Notifications

Les notifications suivants sont gérées par le socle :

| Identifiant | Description | Source | Destination | Arguments |
|---|---|---|---|---|
| TypeEvenement.ETAT_DOMU | Etat du DomU | `DomU` | Tous | `{ "pret" : booléen }` |
| TypeEvenement.DISQUE | Etat d'un disque | `vm-sys-usb` | Tous | `{ "nom" : nom_disque, "connecte": booléen }` |
| TypeEvenement.FICHIER | Etat d'un fichier | `Dom0` | Tous | `{ "fichier" : nom_fichier, "etat": "disponible\|erreur\|copié\|supprimé" }` |
| TypeEvenement.INPUT | Etat d'une entrée clavier, touch ou souris | `vm-sys-usb` | Tous | *Voir la description détaillée* |

### Commandes 

Les commandes suivantes sont gérées par le socle :

| Identifiant | Fonction API | Description | Source | Destination | Type de retour |
|---|---|---|---|---|---|
| TypeCommande.LISTE_DISQUES | `Api.get_liste_disques()` | Demande la liste des disques connectés | DomU | vm-sys-usb | Réponse |
| TypeCommande.LISTE_FICHIERS | `Api.get_liste_fichiers(nom_disque)` | Demande la liste des fichiers d'un disque | DomU | Tous | Réponse | 
| TypeCommande.LIT_FICHIER | `Api.lit_fichier(nom_disque, nom_fichier)` | Copie un fichier depuis un disque vers le dépôt interne | DomU | vm-sys-usb | Notification |
| TypeCommande.COPIE_FICHIER | `Api.copie_fichier(nom_fichier, nom_disque_destination)` | Copie un fichier depuis le dépôt interne vers le disque de destination | DomU | vm-sys-usb | Notification |
| TypeCommande.SUPPRIME_FICHIER | `Api.supprime_fichier(nom_fichier, nom_du_disque = Constantes.DEPOT_LOCAL)` | Supprime un fichier sur un support de stockage (`local` pour le dépôt local) | DomU | Dom0 si local, vm-sys-usb sinon | Notification |

### Réponses

Les messages suivants sont émis en réponse à leurs commandes respectives :

| Identifiant | Description | Arguments | Source | Destination |
|---|---|---|---|---|
| TypeReponse.LISTE_DISQUES | Retourne la liste des disques connectés | Un tableau JSON contenant les noms des disques connectés. | vm-sys-usb | Le domaine émetteur de la commande |
| TypeReponse.LISTE_FICHIERS | Retourne la liste des fichiers d'un disque | Un tableau JSON contenant les chemin et nom des fichiers du disque | vm-sys-usb | Le domaine émetteur de la commande |

## Description détaillée des commandes

Ce chapitre présente une description détaillée des commandes.

### LISTE_DISQUES

- Initiée par : DomU
- Chemin : DomU -> Dom0 -> vm-sys-usb (Réponse : -> Dom0 -> DomU)

La liste des disques est déterminée par la liste des dossiers disponibles dans le répertoire `Constantes.CHEMIN_MONTAGE_USB` et vérifiés par la fonction `os.path.ismount()`.

### LISTE_FICHIERS

- Initiée par : DomU
- Chemin : DomU -> Dom0 -> vm-sys-usb (Réponse : -> Dom0 -> DomU)

La liste des fichiers est initialisée par le domaine `vm-sys-usb` dès la connexion d'un nouveau périphérique (voir notification TypeEvenement.DISQUE). Elle est conservée dans une mémoire cache sur le domaine `vm-sys-usb` pour être retransmise sans délai à la demande.

### LIT_FICHIER

- Initiée par : DomU
- Chemin : DomU -> Dom0 -> vm-sys-usb (Notification : -> Dom0 -> Tous)

La lecture d'un fichier est demandée par un DomU. Celle-ci est traitée par la `vm-sys-usb` et aboutit à la copie du fichier dans le dépôt local sur le Dom0. Lorsque le fichier a été correctement copié, la notification TypeEvenement.FICHIER est émise avec l'état `disponible`.

*La lecture d'un fichier s'accompagne du calcul d'une empreinte numérique stockée dans le dépôt local*.

### COPIE_FICHIER

- Initiée par : DomU
- Chemin : DomU -> Dom0 -> vm-sys-usb (Notification : -> Dom0 -> DomU)

La copie d'un fichier est demandée par un DomU. Celle-ci est traitée par la `vm-sys-usb` et aboutit à la copie du fichier initialement situé dans le dépôt local sur le disque de destination. Lorsque le fichier a été correctement copié, la notification TypeEvenement.FICHIER est émise avec l'état `copié`.

**Pour être copié, un fichier doit d'abord avoir été lu et donc être disponible dans le dépôt local**.

*La copie d'un fichier s'accompagne du calcul d'une empreinte numérique après la copie, et sa comparaison avec l'empreinte originale ainsi que la copie de l'empreinte sur le disque de destination dans un fichier portant le nom du fichier original et l'extension .hash*.

### SUPPRIME_FICHIER

- Initié par : DomU
- Chemin : 
  - DomU -> Dom0 (Notification : -> DomU) si le fichier doit être supprimé sur le dépôt local
  - DomU -> Dom0 -> vm-sys-usb (Notification : -> Dom0 -> DomU) si le fichier doit être supprimé d'un support de stockage externe.

  La suppresion d'un fichier est demandée par un DomU. Celle-ci peut être traitée par le `Dom0` ou par la `vm-sys-usb` en fonction du paramètre `nom_du_disque`. La notification TypeEvenement.FICHIER est émise après la suppression effective, avec l'état `supprimé`.

## Description détaillée des notifications

Ce chapitre présente une description détaillée des notifications.

### INPUT

La notification INPUT indique un changement d'état dans une IHM (clavier, souris ou écran tactile). Sa structure dépend du type d'entrée :

Pour la souris :
```
{
    "entree": "souris",
    "position": { "x": 0, "y": 0 },
    "boutons": {
        "gauche": 1,
        "milieu": 0,
        "droit": 0
    }
}
```

La position est indiquée en valeur absolue en nombre de pixels depuis le coin supérieur gauche.
L'état des boutons est codé par 0 (inactif) ou 1 (actif).

Pour le clavier :
```
{
    "entree": "clavier",
    "touche": "a"
}
```

La notification est émise uniquement dans l'hypothèse où une touche active du clavier a été pressée. Seuls les caractères alphanumériques sont pris en compte.

Pour l'écran tactile :
```
{
    "entree": "tactile",
    "position": { "x": 0, "y": 0 },
    "touche": 0
}
```

La position est indiquée en valeur absolue en nombre de pixels depuis le coin supérieur gauche.
Si l'utilisateur touche l'écran, la variable `touche` sera positionnée à 1, sinon 0.
Les valeurs de `position` et de `touche` évoluent indépendamment. Deux cas de figure sont possibles :
- l'utilisateur fait un simple toucher sur l'écran. Dans ce cas, deux notifications seront émises et la position indiquera l'endroit du toucher, tandis que la valeur de `touche` passera successivement de 1 à 0.
- l'utilisateur opère un glissement du doigt sur l'écran, auquel cas la valeur de `touche` passera à 1 dans la première notification, et la `position` évoluera dans les notifications suivantes, puis la valeur de `touche` passera à 0 tandis que la `position` restera figée sur la dernière position connue.