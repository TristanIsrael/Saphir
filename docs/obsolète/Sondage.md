# Sondage interne

Ce document décrit les spécifications du sondage interne mené dans le but de mieux identifier les différents usages actuels et besoins liés aux stations blanches.

## Questionnaire

Les questions suivantes feront partie du sondage. Les questions en gras sont obligatoires.

**Première partie**
Cette partie a pour objectif de créer des groupes d'utilisateurs ayant des habitudes et/ou des besoins communs et de leur apporter éventuellement une réponse spécifique.

**Q1 - A quelle entité appartenez-vous ?**
*Exemple : DGA/MI/SDTI/ASC1/S2IS*
[Texte libre] 

**Q2 - Quel est votre statut ?**
*Exemple : Architecte, Expert, Officier, Marin, Autre (précisez)*
[Texte libre] 

**Q3 - Décrivez votre environnement de travail :**
*Indiquez si vous travaillez dans un bureau, un laboratoire ou une zone, sur le terrain et dans quelle proportion*

Bureau | xx %
Labo/Zone Diffusion Restreinte | xx %
Labo/Zone Secret | xx %
Labo/Zone Très Secret | xx %
Terrain | xx %

**Q4 - Quels niveaux de protection manipulez-vous ?**
*Indiquez si possible le pourcentage*
[Tableau avec champ numérique entier 0-100 ou vide]

Non protégé | xx %
Diffusion Restreinte | xx %
Secret | xx %
Très Secret | xx %

**Q5 - Quels sont les transferts que vous effectuez ou sur lesquels vous avez des besoins ?**
*Votre réponse ne doit pas tenir compte de vos pratiques actuelles ni des outils actuellement disponibles*
[Cases à cocher]

[] Non protégé <-> Diffusion Restreinte
[] Diffusion Restreinte <-> Secret
[] Diffusion Restreinte <-> Très Secret
[] Secret <-> Très Secret

**Q6 - Quelles sont les volumes habituels ?**
*Indiquez quels volumes de donneés vous avez l'habitude de manipuler. Cette question porte sur le volume total d'un support et non sur les tailles des fichiers.*
[Cases à cocher]

[] 0 - 100 Mo par volume
[] 101 - 500 Mo par volume
[] 501 Mo - 1 Go par volume
[] 1 - 32 Gp par volume
[] 32 - 500 Go par volume
[] > 500 Go par volume

**Q7 - Quelles sont les tailles des fichiers ?**
*Nous cherchons à savoir si vous manipulez surtout ou exclusivement de gros fichiers (images de machines virtuelles par exemple) ou si vous manipulez plutôt de petits fichiers (documents office, fichiers de configuration)
[Boutons radio]

() 0 - 1 Mo par fichier
() 1 - 10 Mo par fichier
() 0 - 1 Mo par fichier
() 1 - 100 Mo par fichier
() 100 - 500 Mo par fichier
() 500 Mo - 1 Go par fichier
() > 1 Go par fichier

**Q8 - Type de support**
*Quels types de support de transfert utilisez-vous ?*
[Cases à cocher]

[] Clé USB
[] Disque dur
[] SSD
[] Carte PCMCIA
[] Autre (précisez)

[Champ de texte] Précisez : 

**Q9 - Nomadisme

**Deuxième partie**
Cette partie du questionnaire a pour objectif de collecter votre opinion sur les équipements et procédés actuels et futurs. L'objectif est de comprendre quel est votre seuil de tolérance et vos besoins spécifiques non couverts.

Q9 - Station blanche actuelle
*Précisez quelle station blanche vous utilisez actuellement*
[Cases à cocher]

[] DGA SNIF
[] DIRISI xxx
[] Autre (préciser)

Q10 - Performance ressentie
*Indiquez si les performances sont acceptables pour vous : à partir de combien de temps l'analyse vous parait trop longue ?*
[Bouton radio]

() 5 minutes
() 15 minutes
() 30 minutes
() 1 heure
() 4 heures
() 1 journée
() pas de limite

Q11 - Durée
*Indiquez la durée moyenne d'un scan.*
[Bouton radio]

() 1 minute
() 5 minutes
() 15 minutes
() 30 minutes
() 1 heure
() 4 heures
() plus de 4 heures

Q11 - Stabilité
*Indiquez si vous réussissez vos scan à chaque fois*
[Case à cocher]

[] Oui
[] Non
[] Je dois l'interrompre parfois

Q12 - Inocuité
*Indiquez si la station blanche détecte correctement les menaces*
[Bouton radio]

() Elle déjà détecté des virus et cela me convient ainsi
() Elle alerte parfois sur des faux-positifs mais cela n'est pas gênant
() Elle alerte parfois sur des faux-positifs et c'est très gênant
() Elle ne détecte pas correctement les virus

*Préciser les cas s'il vous plait : [Texte libre]*