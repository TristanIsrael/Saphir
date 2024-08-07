# Gestion de la journalisation des événements

Ce document présente la stratégie et l'architecture utilisées pour gérer la journalisation des événements du système à des fins de tracabilité et/ou de débogage.

## Besoins

La journalisation couvre deux besoins différents et séparés :
- L'utilisateur doit pouvoir obtenir et transmettre la preuve que ses fichiers ont bien été analysés par le système et que l'inocuité a été vérifiée sur chacun d'eux, et que c'est en toute bonne foi qu'il a utilisé les fichiers du support analysé.
- L'administrateur et le mainteneur du système doivent pouvoir analyser finement le fonctionnement du système dans le cadre des tests de bon fonctionnement (VBF) ou de la recherche d'une panne.
- L'officier de sécurité ou l'analyste en cybersécurité doit pouvoir s'assurer que le système contrôle bien l'intégrité des fichiers de bout-en-bout, depuis le support USB d'origine jusqu'au support USB de destination.

## Stratégie

Les journaux système (les informations émanant des logiciels du système d'exploitation) ne sont pas pris en compte. Seuls les journaux applicatifs sont récupérés. La création d'une entrée dans le journal se fait sur un appel de fonction dans l'API python (`panoptiscan_lib.Api`).

Les entrées de journaux sont traitées localement dans chaque machine virtuelle et remontent automatiquement dans le journal central géré par le service de journalisation du le Dom0.

Le journal étant stocké en mémoire, il est volatile et sera supprimé au prochain redémarrage. Cependant, les applications métier peuvent le consulter par un appel à l'API python et le copier sur le support USB de sortie.

## Architecture

Chaque machine virtuelle DomU possède :
- un canal de communication privilégié avec le Dom0 du type `pv-channel`, fonctionnant comme un **port série** et disponible sur `/dev/hvc2`.
- une API de journalisation qui peut être utilisée au travers de l'Api (`panoptiscan_lib.Api`).

Un appel à l'API permet de générer une entrée de journal qui sera écrite localement sur la sortie standard `stdout` et envoyée sur le canal de communication avec le Dom0. De son côté, le Dom0 surveille les message arrivant depuis les canaux de communication (1 canal par DomU) et aggrège les entrées de journal dans un fichier local unique permettant ainsi de suivre l'évolution d'un traitement sur les différents DomU.

De son côté le Dom0 recoit les messages sur la **socket UNIX (STREAM)** définie dans la configuration du domaine (`xl.conf`). Par convention, chaque DomU doit avoir une socket de journalisation nommée `[nom du domU]-log.sock` dans le répertoire `/var/run/panoptiscan`.

Le service en charge de la gestion de la journalisation côté Dom0 s'appelle `JournalProxy`. Il est fournit dans le paquet Alpine `panoptiscan-socle`.