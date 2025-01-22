# Entrées pour XP SIOC

Ce document contient les entrées demandées par le prestataire dans le cadre du marché XP SIOC III.

## Cas d'usage et contenu de l'IHM

Ces éléments sont disponibles dans le fichier [interface-graphique.md](./interface-graphique.md).

## Autres écran de paramétrage ou d'approvisionnement

Il n'existe pas d'écran de paramétrage.

## Logo et écran splash

Le logo est disponible [ici](../misc/Logo.png). Une version au format `XCF` est disponible dans le même dossier.
L'écran splash est disponible [ici](../misc/splash_1280_800.png). Une version au format `XCF` est disponible dans le même dossier.

## Documentation

La documentation est disponible dans le dossier courant.

La mise en route de l'environnement de développement est décrite dans le fichier [developpement.md](./developpement.md).

## Scénarios de test

Un unique scénario de test permettra de tester l'application :

- Démarrer le système
- Connecter un support USB contenant des fichiers à analyser.
  - Le support doit contenir une arborescence à au moins 3 niveaux et une centaine de fichiers.
  - Le support doit également contenir au moins un fichier infecté (utiliser de préférence le fichier EICAR).
- Lorsque le support est détecté, le navigateur de fichiers est mis à jour et le nom du support est affiché en en-tête ainsi que le contenu de la racine.
- Le bouton de transfert des fichiers n'est pas activé.
- Naviguer dans les répertoires, le contenu de chaque répertoire doit être affiché et les dossiers doivent pouvoir être consultés.
- Sélectionner plusieurs fichiers. La liste des fichiers sélectionnés est mise à jour. La quantité de fichiers sélectionnés est mise à jour.
- Sélectionner un répertoire entier. La liste des fichiers sélectionnés est mise à jour. La quantité de fichiers sélectionnés est mise à jour.
- Démarrer l'analyse.
- Durant l'analyse :
  - Les fichiers en cours d'analyse sont indiqués par une couleur spécifique
  - La progression de l'analyse (pourcentage) et mise à jour
  - Le compte des fichiers infectés et sains augmente
  - Les fichiers sains sont indiqués par une couleur spécifique
  - Les fichiers infectés sont indiqués par une couleur spécifique
  - L'état du système est "analyse en cours"
- A la fin de l'analyse :
  - La somme des fichiers infectés et des fichiers sains égale la quantité de fichiers sélectionnés
  - Tous les fichiers ont un indicateur de couleur
  - La progression de l'analyse est à 100%.
  - L'état du système est "analyse terminée"
- Connecter un second support USB
- Lorsque le support est détecté, le navigateur de fichier est mis à jour et le nom du support est affiché en en-tête. Le contenu n'est pas affiché.
- Le bouton de transfert des fichiers est activé.
- Cliquer sur le bouton de transfert des fichiers.
- Les fichiers sains uniquement sont copiés sur le support de destination.
  - Il n'y a pas de fichier ayant un indicateur d'infection dans le navigateur de sortie.

## Chaines fonctionnelles

Les chaines fonctionnelles sont décrite dans le fichier [conception.md](./conception.md).

## Licence

La licence du produit *`PSEC`* est une licence libre uniquement pour une utilisation individuelle et non-commerciale. Toute autre utilisation du produit est soumise à une licence commerciale.

## Propriété intellectuelle

Le produit `PSEC` sur lequel est basé `Saphir` est la propriété exclusive de `Tristan Israël <tristan.israel@alefbet.net>`. **Son code source ne doit en aucun cas être réutilisé ni communiqué à autrui.**

## Livraison

La livraison inclut les éléments suivants :
- `psec-1.0-py3-none-any.whl` : Bibliothèque PSEC.
- `saphir-1.0.tar.bz2` : Code source et documentation de Saphir.