# Architecture logicielle

Ce document présente l'architecture logicielle de Panoptiscan.

## Vue d'ensemble

TODO

## Gestion des paramètres

Les paramètres sont gérés à deux niveaux :
- constantes
- configuration.

Les constantes sont gérés dans la classe `Constantes` et peuvent être considérées soit comme des valeurs universelles, soit des valeurs *par défaut*. 

Les configurations sont gérées dans le fichier de configuration local au Domaine (`/etc/panoptiscan/local.conf`) et constituent soient des définitions locales propres au contexte, soit des valeurs surchargeant celles des constantes.

Dans tous les cas, l'obtention d'une valeur passe par la classe `Parametres`. La fonction `Parametres::parametre()` retournera prioritairement la valeur locale, puis la valeur définie dans la classe `Constantes` en cas d'absence, ou `None` si aucune valeur n'est définie (la clé n'existe pas).

Tous les paramètres doivent être définis par une clé enregistrée dans la classe `Parametres::Cles`.