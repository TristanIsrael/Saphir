# Benchmark du système

Ce document présente les différents mécanismes mis en oeuvre pour mesurer les performances du système dans différentes conditions (notamment matérielles).

Les objectifs du benchmark sont :
- de disposer d'indicateurs de performances permettant 
- d'établir une norme de performances
- comparer différentes instances du système entre elles et avec la configuration de référence. Cette dernière étant réputée fonctionner correctement.
- identifier les pistes d'optimisation des composants du socle.

## Benchmark Matériel

Ce chapitre contient des informations permettant de comparer les performances des différentes configurations matérielles.
Seules les performances CPU et RAM sont mesurées.

### Protocole 

Installer l'outil `lzbench`
Créer un fichier : `dd if=/dev/urandom of=/tmp/bench.in bs=1 count=1048000`
Exécuter la commande suivante : `lzbench -ezstd /tmp/bench.in`

### Machine virtuelle x86_64@arm64

Configuration physique : Macbook Pro M2 2022
Hyperviseur : UTM
Configuration emulée : 
  - Standard PC (pc-q35-7.2), 
  - arch x86_64, 
  - 4Go RAM
  - CPU Nehalem-v2 avec vmx (Intel Core i7 9xx & 2.0Ghz)
  - Bogomips : 2000
  - 1 CPU, 1 coeur
  - Carte graphique CIRRUS

#### Résultats 

  `lzbench 1.8 (64-bit Linux)   Assembled by P.Skibinski`

| Compressor name | Compress. | Decompress. | Compr. size  | Ratio Filename |
|--|--|--|--|--|
| memcpy |                  4578 MB/s | 5140 MB/s  |   1048576 | 100.00 | bench.in |
| zstd 1.4.5 -1 |             242 MB/s | 5017 MB/s  |   1048610 | 100.00 | bench.in |
| zstd 1.4.5 -2 |             236 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -3 |             225 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -4 |             222 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -5 |              95 MB/s | 5041 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -6 |            100 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -7 |             99 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -8 |             97 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -9 |            103 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -10 |            94 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -11 |            96 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -12 |            94 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -13 |            83 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -14 |            83 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -15 |            82 MB/s | 4993 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -16 |          8.90 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -17 |          8.40 MB/s | 5017 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -18 |          4.93 MB/s | 4877 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -19 |          4.73 MB/s | 4922 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -20 |          4.71 MB/s | 4993 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -21 |          4.56 MB/s | 4993 MB/s  |   1048609 | 100.00 | bench.in |
| zstd 1.4.5 -22 |          4.65 MB/s | 4899 MB/s  |   1048609 | 100.00 | bench.in |
`done... (cIters=1 dIters=1 cTime=1.0 dTime=2.0 chunkSize=1706MB cSpeed=0MB)`

**Moyenne : environ 5000 MB/s**

### PC Dell Vostro xxx

Configuration physique : Dell Vostro XXX 
  - arch x86_64, 
  - 4Go RAM,
  - CPU Celeron XXX,
  - Bogomips : 2394,
  - 1 CPU, 2 coeurs,
  - Carte graphique XXX

#### Résultats 

| Compressor name         | Compression| Decompress.| Compr. size | Ratio | Filename |
| ---------------         | -----------| -----------| ----------- | ----- | -------- |
| memcpy                  |  4476 MB/s |  4203 MB/s |     1048000 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -1           |  1130 MB/s |  4173 MB/s |     1048034 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -2           |  1091 MB/s |  4185 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -3           |   868 MB/s |  4183 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -4           |   800 MB/s |  4187 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -5           |   476 MB/s |  4176 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -6           |   458 MB/s |  4173 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -7           |   411 MB/s |  4175 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -8           |   416 MB/s |  4180 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -9           |   372 MB/s |  4179 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -10          |   345 MB/s |  4180 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -11          |   339 MB/s |  4178 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -12          |   334 MB/s |  4183 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -13          |  36.8 MB/s |  4165 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -14          |  36.9 MB/s |  4183 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -15          |  36.8 MB/s |  4178 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -16          |  5.73 MB/s |  4178 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -17          |  5.68 MB/s |  4164 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -18          |  4.70 MB/s |  4174 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -19          |  4.23 MB/s |  4175 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -20          |  4.27 MB/s |  4156 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -21          |  4.24 MB/s |  4157 MB/s |     1048033 |100.00 | /tmp/bench.in|
| zstd 1.5.5 -22          |  4.34 MB/s |  4172 MB/s |     1048033 |100.00 | /tmp/bench.in|

  **Moyenne : 4170 MB/s**

## Benchmark socle

Ce chapitre présente les résultats de benchmark sur le socle.

Pour rappel, les flux de communications s'appuient sur différents protocoles circulant au travers du Xenbus :
- *inputs* : Communication série pvchan indirecte DomU <-> Dom0 <-> DomU.
- *commandes* : Communication série pvchan indirecte DomU <-> Dom0 <-> DomU.
- *fichiers* : Protocole P9.

### Matériel

#### PC Dell Latitude E5510

  Configuration physique : Dell Latitude E5510
  - arch x86_64, 
  - 8Go RAM,
  - CPU Core i5 ,
  - Bogomips : 2394,
  - 1 CPU, 2 coeurs,
  - Carte graphique XXX

  Xen version 4.18.2

### Inputs

La mesure est réalisée de bout-en-bout, le benchmark ne s'intéresse pas aux performances des étapes intermédiaires, en particulier celles du contrôleur du Dom0.
Le benchmark du canal *inputs* consiste à envoyer une série de 1000 déplacements de souris successifs.

Les métriques sont :
- durée totale d'émission,
- durée totale de réception,
- quantité d'itérations émises,
- quantité d'itérations reçues,
- quantité de positions par seconde,
- quantité de positions par seconde à chaque seconde.

Le benchmark est déclenché par l'application de diagnostic grâce à la commande `start_benchmark` avec l'argument `inputs`.
Lorsque la `vm-sys-usb` recoit cette commande, elle démarre l'émission des positions, puis lorsque toutes les positions ont été émises,
elle envoie la réponse `end_benchmark` avec comme données la structure suivante :
```
{
    "start_date": 1234567890,
    "end_date": 1234567890,
    "iterations": 1000
}
```

| Champ | Commentaire |
|---|---|
| start_date | Date du démarrage du benchmark en millisecondes depuis EPOCH |
| end_date | Date de la fin de l'exécution du benchmark en millisecondes depuis EPOCH |
| iterations | Nombre d'itération exécutées (quantité de positions transmises) |

**Résultats**

| Matériel | Itérations | Durée émission | Débit |
|---|---|---|---|
| QEMU x86_64 sur Mac M2 | 1000 | 811 ms | 123 itérations/cs |
| Dell Latitude E5510 Core i5 | 1000 | 117 ms | 854 itérations/cs |

### Transferts de fichiers

La mesure du débit peut se faire à plusieurs points et de bout-en-bout :

| Sens | Mesure |
|---|---|
| support USB -> VM sys-usb | Débit de lecture de l'interface USB |
| VM sys-usb -> dépôt | Débit du transfert 9P |
| dépôt -> VM diagnostic | Débit du transfert 9P |
| VM sys-usb -> support USB | Débit d'écriture de l'interface USB |

Le scénario mis en oeuvre est le suivant :
| Opération | Indicateur |
|---|---|
| Ecriture d'un fichier d'une taille de `n` octets sur le support USB d'entrée | Débit moyen d'écriture USB |
| Lecture du fichier depuis le support USB vers la RAM | Débit moyen de lecture USB |
| Transfert du fichier depuis le support USB vers le dépôt | Débit moyen d'écriture 9P |
| Lecture du fichier depuis le dépôt vers la RAM | Débit moyen de lecture 9P |

Les tests sont effectués avec plusieurs tailles et quantités de fichiers :
| Taille | Quantité | Volume total (Mo) |
|---|---|---|
| 10 Ko | 100 | 1 Mo |
| 100 Ko | 100 | 10 Mo |
| 500 Ko | 100 | 50 Mo |
| 1 Mo | 10 | 10 Mo |
| 10 Mo | 10 | 100 Mo |
| 100 Mo | 10 | 1 Go |
| 500 Go | 2 | 1 Go |
| 1 Go | 1 | 1 Go |

Les métriques affichées sont :
- Débit de la lecture USB
- Débit 9P entre VM sys-usb et dépôt
- Débit 9P entre dépôt et VM diag
- Débit de l'écriture USB

**Résultats**

*Les débits sont exprimés en Mo/s*

#### QEMU x86_64@Mac M2

| | 10 Ko | 100 Ko | 500 Ko | 1 Mo | 10 Mo | 100 Mo |
|--|--|--|--|--|--|--|
| Ecriture USB | 1,37 | 7,87 | 6,88 | 20,71 | 3,89 | 2,83 |
| Lecture USB | 2,52 | 17,79 | 61,10 | 98,12 | 157,53 | 8,55 |
| Ecriture dépôt | 0,08 | 0,82 | 3,25 | 5,76 | 14,13 | 9,57 |

#### Dell Latitude E5510

| | 10 Ko | 100 Ko | 500 Ko | 1 Mo | 10 Mo | 100 Mo |
|--|--|--|--|--|--|--|
| Ecriture USB | 20,2 | 80,02 | 21,08 | 6,13 | 2,54 | 3,59 |
| Lecture USB | 44,4 | 282,02 | 798,67 | 997,49 | 1389,78 | 15,88 |
| Ecriture dépôt | 1,17 | 12,19 | 51,47 | 95,83 | 107,35 | 17,08 |

## Commandes

Ce chapitre traite des performances de certaines commandes.

### SHA256

Cette section compare les performance du calcul d'empreinte pour différents algorithmes et implémentations de ces algorithmes.

**Résultats**

| Commande | Environnement | Taille | Durées (3 runs) | Débit |
|--|--|--|--|--|
| md5sum | Alpine Linux 3.20 sur Dell Latitude E5519 | 100 Mo | 0,29s ; 0,29s ; 0,29s | 344,83 Mo/s |
| sha256 | Alpine Linux 3.20 sur Dell Latitude E5519 | 100 Mo | 0,77s ; 0,77s ; 0,79s | 128,21 Mo/s |
| sha512 | Alpine Linux 3.20 sur Dell Latitude E5519 | 100 Mo | 0,5s ; 0,51s ; 0,5s | 200 Mo/s |
| md5sum | hashlib.file_digest("md5") | 100 Mo | 0,2s ; 0,19s ; 0,2s | 500 Mo/s |
| sha256 | hashlib.file_digest("hash256") | 100 Mo | 0,44s ; 0,45s ; 0,44s | 227 Mo/s |
| sha512 | hashlib.file_digest("hash512") | 100 Mo | 0,35s ; 0,35s ; 0,35s | 286 Mo/s |

| Commande | Environnement | Taille | Durées (3 runs) | Débit |
|--|--|--|--|--|
| md5sum | Alpine Linux 3.20 sur Dell Latitude E5519 | 3 Go | 8,21s ; 8,22s ; 8,26s | 373 Mo/s |
| sha256 | Alpine Linux 3.20 sur Dell Latitude E5519 | 3 Go | 25,5s ; 22,9s ; 22,8s | 131 Mo/s |
| sha512 | Alpine Linux 3.20 sur Dell Latitude E5519 | 3 Go | 14,6s ; 14,7s ; 14,6s | 210 Mo/s |
| md5sum | hashlib.file_digest("md5") | 3 Go | 5,58s ; 5,58s ; 5,54s | 553 Mo/s |
| sha256 | hashlib.file_digest("hash256") | 3 Go | 13,14s ; 13,11s ; 13,09s | 234 Mo/s |
| sha512 | hashlib.file_digest("hash512") | 3 Go | 10,26s ; 10,30s ; 10,24s | 299 Mo/s |

**Observations**
- Les débit semblent à peu près constants (5-8% de différence en débit pour un facteur 300 sur la taille)
- SHA512 est plus rapide que SHA256
- MD5 est plus rapide que SHA*
- `Python.hashlib` est plus rapide que la ligne de commande