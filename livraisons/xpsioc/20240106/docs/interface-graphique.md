# Interface graphique

Ce document décrit les objets et états de l'interface graphique de Saphir.

## Périphériques

Les actions de l'utilisateur peuvent être réalisés avec un ou plusieurs supports, y compris dans une même session :

- Souris à 2 boutons et molette (+1 bouton sous la molette)
- Ecran tactile permettant le positionnement, le toucher et le glissement uniquement.

L'ergonomie des interactions avec le système doit respecter les standards en vigueur sur les appareils grand public.

## Modes d'affichage

Deux modes d'affichage sont possibles :

- Normal jour : utilisation normals en intérieur ou de jour.
- Basse visibilité : utilisation en environnement furtif nécessitant la plus grande discrétion.
- Automatique : bascule d'un mode d'affichage à l'autre en fonction de la luminosité.

L'interface graphique de Saphir est toujours affichée en plein écran et de façon modale. Il n'est pas possible de basculer sur une autre application.

## Codes couleurs et charte graphique

Aucune charte graphique n'est imposée. Cependant certains codes couleurs et thèmes doivent être utilisés :
- Erreur / ocuité : la couleur doit être dérivée du rouge.
- Succès / Validation / inocuité : la couleur doit être dérivée du vert.
- Le thème de couleur doit utiliser les couleurs principales du logo et du splash :
  - bleu (évocation du saphir)
  - gris
  - blanc
  
## Objets et indicateurs

Cette section décrit les indicateurs.

| Indicateur | Valeurs type | Description |
|--|--|--|
| Niveau de sécurité | `DR`, `S`, `TS` | Indique le niveau de sécurité maximum autorisé sur le système |
| Nom du produit | `Saphir` | Le nom du produit doit apparaître avec la police `Freshbot` |
| Heure courante | `HH:mm` | L'heure courante est affichée en permanence |
| Support d'entrée | `Nom du support` | Le support d'entrée doit apparaître clairement séparé du support de sortie |
| Fichiers du support d'entrée | | La liste des fichiers du support d'entrée doit être navigable comme un explorateur de fichiers et afficher le nom et l'extension des fichiers du dossier courant. |
| Fichiers sélectionnés pour analyse | | La liste des fichiers sélectionnés pour analyse doit apparaître clairement séparée des supports d'entrée et de sortie. |
| Info-bulles d'aide | | L'utilisateur peut afficher les info-bulles lui permettant de comprendre la fonction de chaque objet affiché à l'écran |
| Type de support | `IN` | Un indicateur visuel permet d'identifier si le support est le support d'entrée ou de sortie |
| Avancement de l'analyse (%) | `25%` | Un indicateur visuel du type barre de progression doit permettre à l'utilisateur d'identifier la progression de l'analyse. |
| Quantité de fichiers sélectionnés pour analyse | `3443` | Un indicateur numérique doit permettre d'identifier la quantité totale de fichiers sélectionnés |
| Quantité de fichiers sains | `3244` | Un indicateur numérique doit permettre d'identifier la quantité de fichiers analysés sains |
| Quantité de fichiers infectés | `199` | Un indicateur numérique doit permettre d'identifier la quantité de fichiers analyses infectés |
| Nettoyage en cours / Préparation en cours | | Le système est en train d'être nettoyé ou préparé pour une nouvelle analyse |
| Arrêt en cours | | Le système est en cours d'exctinction, plus aucun action n'est possible |
| Etat du système | `Démarrage en cours` | Un indicateur présente textuellement l'état du système (Démarrage en cours, système prêt, ...) |
| Mode d'affichage | `auto` | Un indicateur permet de connaitre le mode d'affichage courant (peut-être fusionné avec le bouton d'action associé) |
| Niveau de charge batterie | `30%` | Un indicateur permer de connaître le niveau de charge de la batterie |
| Alimentation secteur | | Un indicateur permet de savoir si l'appareil est actuellement en charge. *Cet indicateur peut être fuctionné avec le niveau de charge de la batterie*. |
| Etat des composants du système | Un indicateur doit permettre de connaitre l'état de l'ensemble des composants du système |

## Actions 

| Action | Description |
|--|--|
| Navigation dans un dossier de l'arborescence | Quand l'utilisateur clique sur un dossier, le contenu de celui-ci est affiché dans le navigateur à la place du dossier parent. |
| Retour au dossier supérieur | Quand l'utillisateur clique sur le bouton de retour au dossier précédent, le contenu de celui-ci est affiché à la place du dossier courant. |
| Sélection d'un fichier du support d'entrée | Un fichier doit pouvoir être sélectionné pour analyse à la souris ou au doigt. La sélection se fait en un clic sur un bouton associé au fichier ou sur le nom du fichier (à définir). |
| Sélection de tous les fichiers du dossier courant | Une action spécifique permet de sélectionner en une seule fois tous les fichiers du dossier courant. |
| Sélection de tous les fichiers du disque | Une action spécifique permet de sélectionner en une seule fois tous les fichiers du support d'entrée |
| Démarrage de l'analyse | Une action spécifique permet de démarrer l'analyse des fichiers sélectionnés |
| Mise en pause/arrêt de l'analyse | Une action permet de mettre en pause ou arrêter l'analyse |
| Afficher l'aider | Une action spécifique permet à l'utilisateur d'afficher l'aide (sous la forme d'info-bulles) |
| Arrêt du système | Une action spécifique permet à l'utilisateur d'arrêter complètement le système et la machine |
| Redémarrage / nettoyage du système | Une action spécifique permet de nettoyer le système avant de procéder à l'analyse d'un autre support |
| Transfert des fichiers | Une action spécique permet à l'utilisateur de transférer les fichiers sur le support de sortie |
| Changement du mode d'affichage | Une action spécifique permet à l'utilisateur de basculer entre les modes d'affichage |
| Affichage de l'état des composants | Une action spécifique permet à l'utilisateur d'afficher la listee des composants du système (antivirus 1, antivirus 2, accès disque, coeur, ...) et leur état (démarrage, normal, erreur) |
| Affichage du journal | Une action spécifique permet à l'utilisateur d'afficher le journal du système |

## Etats

| Etat | Description |
|--|--|
| Pas de support d'entrée | Aucun support d'entrée identifié |
| Support d'entrée incompatible | Le support d'entrée ne peut pas être utilisé |
| Pas de support de sortie | Aucun support de sortie identifié |
| Support de sortie incompatible | Le support de sortie ne peut pas être utilisé |
| Fichier sélectionné pour analyse | Le fichier est sélectionné et en attente d'analyse |
| Fichier en cours d'analyse | Le fichier est en cours d'analyse par un ou plusieurs antivirus (les antivirus peuvent passer successivement sur le même fichier) |
| Fichier sain | Le fichier a été analysé comme sain |
| Fichier infecté | Le fichier a été analysé comme infecté ou une erreur s'est produite lors de son analyse. |
| Fichier en cours de copie | Le fichier est en cours de copie sur le support cible |
| Fichier copié | Le fichier a été copié sur le support cible |

## Interactions

## Particularités / Discussions

- L'analyse d'un fichier est réalisée par plusieurs antivirus. Les indicateurs de progression et d'état des fichiers doivent tenir compte de cette particularité. Par exemple : un fichier est analysé par un premier antivirus, son état va passer en cours d'analyse, et la progression va augmenter jusqu'à 100%, mais cela ne représente qu'une fraction de l'analyse qui doit être faite sur ce fichier puisque *n* antivirus passeront dessus. 
- L'état d'inocuité d'un fichier est défini en fonction de la plus mauvaise situation : si le fichier est analysé comme sain par tous les antivirus, son état est `sain`, dans tous les autres cas (erreur, infection) son état est `infecté`.
- La mise en pause ou l'arrêt de l'analyse est un sujet à discuter au niveau de l'ergonomie. Faire le point sur les cas d'usage associés pour ne conserver que les actions utiles.