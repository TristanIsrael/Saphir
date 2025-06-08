# Tests

Ce document décrit la campagne de tests de non-régression et de performances.

## Stratégie

La stratégie de tests consiste à tester les fonctionnalités critiques du système à chaque incrément ainsi qu'une sélection de tests de non-régression. 
Des tests de performance (célérité) sont également réalisés pour identifier une éventuelle perte de performance d'un incrément à un autre ou
suite à une mise à jour du socle.

## Jeux de données

L'ensemble des tests doit être joué avec le même jeu de données pour être représentatif. Ce chapitre décrit les jeux de données de tests.

### Malwares

Un jeu de données spécifique aux détections est construit sur la base des malwares fournis par 

### Performances

Le jeu de données est constitué par le script `create-files.py`.

Ce script a pour objectif de remplir un support de stockage avec des fichiers de taille aléatoire (1 Ko à 50 Mo) et de nature variables (90% binaire et 10% archives compressées). Les archives contiennent 10 niveaux de répertoires imbriqués et chaque répertoire contient 1 fichier binaire d'une taille aléatoire.

Description du jeu de données :
```
Volume total : 15 338 816 Ko.
Formattage : FAT32
Fichiers : 610
dont :
  - .bin : 537 (88 %)
  - .zip : 14
  - .7z : 6
  - .gz : 6
  - .bzip2 : 16
  - .xz : 16
  - .lz4 : 15
```

Le système doit pouvoir analyser la totalité des fichiers et ne détecter aucun virus.

### Malwares

Les tests de détection sont réalisés à partir de malwares réels obtenus sur le site [malware bazaar](https://bazaar.abuse.ch/).

Le jeu de données contient `100` fichiers qui doivent tous être detectés par le système.
Volume total : `424 516 Ko`.

Le jeu de données est constitué par le script `download-malwares.py`. Il dépend du projet GitHub [malware-bazaar](https://github.com/cocaman/malware-bazaar/tree/master).

## Plans de tests

Ce chapitre décrit les plans de tests pour le système.

### Tests critiques minimaux

| Ident. | Nom | Description |
|--|--|--|
| TCM-1 | Détection des fichiers infectés | Analyse du jeu de données malware et détection de l'ensemble des menaces |

### Non-régression

| Ident. | Nom | Description |
|--|--|--|
|  |  |  |

### Performances

| Ident. | Nom | Description |
|--|--|--|
| PERF-1 | Durée du démarrage | Mesure la durée du démarrage du système depuis le menu GRUB jusqu'à son état prêt. |
| PERF-2 | Durée de l'analyse | Mesure la durée de l'analyse du jeu de données performances. |

## Campagnes

Ce chapitre recense les campagnes de tests significatives permettant de conserver un historique des performances.

### Version 1.0 - juin 2025

Environnement de test : 
- Durabook R8 Core i5 8Go. 
- Source d'énergie : secteur.

| Test | Actions | Résultat attendu | Résultat obtenu | Succès | Notes |
|--|--|--|--|--|--|
| PERF-1 | Démarrage du système. | < 1' | 1'34 | Non | |
| PERF-2 | Analyse du jeu de données performance | 610 fichiers analysés, aucune menace. | Durée : | | 727 fichiers ? |
| TCM-1 | Analyse de l'ensemble du jeu de données malwares | Détection de 100 fichiers infectés, aucun fichier non infecté. Aucun fichier copié sur le deuxième support. | | | |