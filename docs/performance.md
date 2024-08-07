# Performance

Ce document décrit les éléments stratégiques relatifs à la performance du système.

## Objectifs

La performance est exprimée sous deux aspects :
- la satisfaction des besoins de l'utilisateur (besoins primaires de l'utilisateur)
- la vitesse d'exécution (besoin secondaire de l'utilisateur)

La stratégie est basée sur l'égale satisfaction de ces deux aspects.

## Besoins de l'utilisateur

Les besoins de l'utilisateur sont :

| Référence | Besoin | Catégorie |
|---|---|---|
| B#1 | Vérifier l'inocuité de certains fichiers | Primaire |
| B#2 | Copier les fichiers sains sur un support de niveau supérieur | Primaire |
| B#3 | Obtenir un résultat le plus rapidement possible | Secondaire |

## Stratégie

La stratégie permettant de satisfaire les besoins B#1, B#2 et B#3 en même temps consiste à analyser les fichiers dès leur sélection, à paralléliser autant que possible leur analyse par les différents antivirus et à copier les fichiers sur le support de destination dès que leur inocuité à été vérifiée.

## Capacité du matériel

Les performances techniques du matériel ont un impact décisif sur l'objectif B#3. Si le matériel dispose de beaucoup de mémoire et d'un processeur très puissant, il sera possible d'analyser plus de fichiers en parallèle.

Le système est conçu pour être en capacité de travailler avec les matériels peu dotés. Pour ce faire, l'analyse fonctionne selon l'approche des flux tirés avec un *Kanban*. Le *Kanban* est calculé en fonction des capacités matérielles et détermine la quantité de fichiers qui peuvent être analysés en parallèle. 

Si le matériel comporte peu de mémoire et/ou un faible processeur, le kanban aura une taille de 1 fichier. Sur un matériel très puissant, il pourra monter entre 2 et 4 fichiers.

De plus, la taille du *kanban* pourra être ajustée automatiquement pendant le fonctionnement afin de maximiser l'utilisateur des ressources matérielles et réduire la durée du traitement. Cette optimisation est rendue possible par le calcul d'un débit de traitement de bout-en-bout (lecture du fichier -> analyse -> copie) et sa comparaison avec l'utilisation des ressources matérielles (charge système et RAM).