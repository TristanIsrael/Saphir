# Conception de Saphir

Ce document décrit les principaux éléments de conception du produit Saphir.

## Chaines fonctionnelles

Ce chapitre décrit les chaines fonctionnelles du produit.

### [CIN] Chaine d'initialisation

La chaine d'initialisation permet à l'administrateur de créer un nouveau produit à partir d'un matériel sur étagère.

Les fonctions de la chaine sont :
- Démarrage du processus via le réseau (PXE)
- Téléchargement des paquets d'installation du système
- Validation de l'empreinte numérique du support
- Validation de la conformité du matériel
  - MVP : uniquement un placeholder (= pas de validation)
- Installation du système en mémoire
- Affichage de l'interface graphique

### [CAP] Chaine d'approvisionnement

La chaine d'approvisionnement permet à l'administrateur d'approvisionner un matériel pour en faire un produit viable ou de recycler un produit déjà utilisé pour le mettre à son état initial.

Cette chaîne est strictement identique à la **Chaine d'initialisation**.

### [CAV] Chaine d'analyse antivirale

La chaine d'analse antivirale permet à l'utilisateur final de sélectionner et analyser les fichiers d'un support de stockage qui souhaite analyser.

*Cette chaine est exécutée autant de fois que le nombre d'antivirus mis en oeuvre sur le système*.
 
Fonctions :
- Réception d'une demande d'analyse par la GUI [param = liste de fichiers]
- Pour chaque fichier :
  - Calcul de l'empreinte numérique du fichier en entrée
  - Analyse antivirale
  - Notification du résultat de l'analyse
  - Calcul de l'emprinte numérique du fichier en sortie
- Mise en quarantaine d'un fichier infecté
- Inscription d'une entrée dans le fichier journal

Performances :
- Si la mémoire est suffisante, il faut paralléliser les analyses sur les *n* antivirus.
- Si la mémoire est insuffisante, il faut sérialiser les analyses sur les *n* antivirus.

### [CCF] Chaine de copie de fichiers

La chaine de copie de fichiers permet à l'utilisateur final de copier les fichiers sains sur un support de stockage autre que le support d'entrée.

Fonctions :
- Calcul de l'empreinte numérique du fichier en entrée
- Transfert d'un fichier depuis la source vers la cible
- Notification de la GUI après la copie (succès, erreur)
- Calcul de l'empreinte numérique du fichier en sortie
- Inscription d'une entrée dans le fichier journal

### [CMJ] Chaine de mise à jour (= chaine d'approvisionnement)

La chaine de mise à jour permet de maintenir le système en condition opérationnelle et en condition de sécurité.

*Cette chaine est strictement identique à la chaine d'approvisionnement*.

### [CNO] Chaine de nomadisation

La chaine de nomadisation permet de transformer un système sédentaire démarré par le réseau en un système capable d'être démarré déconnecté du réseau.

*Cette chaine est déclenchée automatiquement à la condition qu'un paramètre d'environnement soit fourni au démarrage*.

Fonctions :
- Initialisation du disque embarqué
- Copie des fichiers d'installation sur le disque embarqué
- Calcul de l'empreinte numérique du support
- Validation de l'empreinte numérique du support
- Stockage de l'empreinte numérique du support

### [CAR] Chaine d'arrêt

La chaine d'arrêt permet d'arrêter le système en s'assurant qu'il retourne à son état initial et qu'il soit intègre.
 
Fonctions :
- Réception d'une demande d'arrêt
- Arrêt et extinction du système
- Vérification de l'intégrité du système (absence d'altération des paquets d'installation et configuration)


