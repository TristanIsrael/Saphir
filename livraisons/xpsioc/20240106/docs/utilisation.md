# Utilisation

Ce document explique l'utilisation de la station blanche.

## Démarrage

A détailler.

## Etat initial

Après la séquence de démarrage, le dispositif se trouve dans son état initial. Il est identique sur tous les appareils.

Quand il est dans son état initial, le dispositif affiche l'écran d'accueil demandant à l'utilisateur de connecter un support à analyser.

L'analyse des fichiers est démarrée, cela signifie que dès qu'un premier fichier est ajouté à la liste des fichiers à analyser, il sera automatiquement analysé.

## Connexion d'un support par l'utilisateur

Lorsque l'utilisateur connecte un support, le dispositif récupère la liste des fichiers et la présente à l'utilisateur sous la forme d'un navigateur de fichiers. Le premier support connecté est automatiquement considéré comme le support à analyser.

Si l'utilisateur connecte un second support, celui-ci sera considéré comme la destination. Le dispositif n'affichera pas la liste des fichiers qu'il contient.

## Sélection de fichiers par l'utilisateur

A chaque fois que l'utilisateur sélectionne un fichier à analyser, celui-ci est automatiquement ajouté à la liste des fichiers à analyser.

L'analyse des fichiers démarre dès la sélection du premier fichier. Si l'utilisateur ajoute des fichiers, ils seront ajoutés à la liste des fichiers à analyser.

En fonction des capacités techniques du matériel, plusieurs fichiers seront analysés simultanément.

### Présence de deux supports

Si l'utilisateur a connecté deux supports, la copie des fichiers sains démarre automatiquement sur le support de destination.

## Contrôle de l'utilisateur

Durant l'analyse des fichiers, l'utilisateur peut :
- mettre en pause l'analyse des fichiers.
- arrêter l'analyse des fichiers, ce qui a pour conséquence de réinitialiser partiellement le dispositif pour permettre une nouvelle analyse.
- reprendre l'analyse mise en pause.
- ajouter des fichiers à la liste des fichiers à analyser.

## Fin de la séquence

La séquence d'analyse ne s'arrête que lorsque :
- l'utilisateur arrête l'analyse en appuyant sur le bouton d'arrêt, ce qui a pour conséquence de réinitaliser partiellement le dispositif.
- l'utilisateur éteint le dispositif.

Lorsque la séquence d'analyse est terminée, le fichier journal est automatiquement copié sur le support de destination.

### Connexion d'un second support après analyse

Si l'analyse des fichiers est terminée et que l'utilisateur connecte un second support, la copie des fichiers sains et du journal débute automatiquement.

L'utilisateur peut encore ajouter des fichiers à analyser s'il le souhaite.

