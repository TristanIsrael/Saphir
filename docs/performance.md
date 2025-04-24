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

## Optimisation de la mémoire

Les fichiers suivants peuvent être supprimés après le démarrage (si OpenGL n'est pas utilisé):
- /usr/lib/gallium-pipe/pipe_iris.so
- /usr/lib/gallium-pipe/pipe_crocus.so
- /usr/lib/gallium-pipe/pipe_radeonsi.so
- /usr/lib/gallium-pipe/pipe_nouveau.so
- /usr/lib/gallium-pipe/pipe_r300.so
- /usr/lib/gallium-pipe/pipe_vmgfx.so
- /usr/lib/gallium-pipe/pipe_r600.so
- /usr/lib/gallium-pipe/pipe_i915.so

Les fichiers suivants peuvent être supprimés après le démarrage (si OpenGL est utilisé):
- /usr/lib/gallium-pipe/pipe_swrast.so
- tous les drivers qui ne correspondent pas au GPU de l'hôte

Les paquets suivants peuvent être supprimés après le démarrage :
- qt6-qtwebengine

Commande de suppression des fichiers d'un paquet : `apk info -L <nom_du_paquet> | xargs -I {} rm -rf {}`

###

Downloading llvm19-libs-19.1.4-r1
Downloading mbedtls-3.6.3-r0
Downloading mesa-24.2.8-r0##
Downloading mesa-dri-gallium-24.2.8-r0###
Downloading mesa-egl-24.2.8-r0###########
Downloading mesa-gbm-24.2.8-r0###########
Downloading mesa-gl-24.2.8-r0############
Downloading mesa-glapi-24.2.8-r0#########
Downloading minizip-1.3.1-r0#############
Downloading mkfontscale-1.2.3-r1#########
Downloading mpg123-libs-1.32.9-r0########
Downloading mtdev-1.1.7-r0###############
Downloading nettle-3.10-r1###############
Downloading nghttp2-libs-1.64.0-r0#######
Downloading nspr-4.36-r0#################
Downloading nss-3.109-r0#################
Downloading numactl-2.0.18-r0#############
Downloading onevpl-libs-2023.3.1-r2#######
Downloading openexr-libiex-3.3.2-r0#######
Downloading openexr-libilmthread-3.3.2-r0#
Downloading openexr-libopenexr-3.3.2-r0###
Downloading openexr-libopenexrcore-3.3.2-r0
Downloading openjpeg-2.5.2-r0##############
Downloading openxr-1.1.43-r0###############
Downloading opus-1.5.2-r1##################
Downloading orc-0.4.40-r1##################
Downloading p11-kit-0.25.5-r2##############
Downloading pango-1.54.0-r1################
Downloading pcre2-10.43-r0#################
Downloading pixman-0.43.4-r1###############
Downloading pkgconf-2.3.0-r0###############
Downloading psec-gui-base-1.0-r1###########
Downloading py3-brotli-1.1.0-r2############
Downloading py3-brotli-pyc-1.1.0-r2#########
Downloading py3-cffi-1.17.1-r1##############
Downloading py3-cffi-pyc-1.17.1-r1##########
Downloading py3-cparser-2.22-r1#############
Downloading py3-cparser-pyc-2.22-r1#########
Downloading py3-cssselect2-0.7.0-r5#########
Downloading py3-cssselect2-pyc-0.7.0-r5#####
Downloading py3-fonttools-4.55.0-r0#########
Downloading py3-fonttools-pyc-4.55.0-r0######
Downloading py3-humanize-4.9.0-r1#############
Downloading py3-humanize-pyc-4.9.0-r1#########
Downloading py3-jinja2-3.1.6-r0###############
Downloading py3-jinja2-pyc-3.1.6-r0###########
Downloading py3-markupsafe-3.0.2-r0###########
Downloading py3-markupsafe-pyc-3.0.2-r0#######
Downloading py3-pillow-11.0.0-r0##############
Downloading py3-pillow-pyc-11.0.0-r0##########
Downloading py3-pydyf-0.11.0-r0###############
Downloading py3-pydyf-pyc-0.11.0-r0###########
Downloading py3-pyphen-0.17.0-r0##############
Downloading py3-pyphen-pyc-0.17.0-r0###########
Downloading py3-pyside6-6.8.0.2-r0#############
Downloading py3-shiboken6-6.8.0.2-r0#################
Downloading py3-tinycss2-1.4.0-r0#####################
Downloading py3-tinycss2-pyc-1.4.0-r0#################
Downloading py3-tinyhtml5-2.0.0-r0####################
Downloading py3-tinyhtml5-pyc-2.0.0-r0################
Downloading py3-webencodings-0.5.1-r8#################
Downloading py3-webencodings-pyc-0.5.1-r8#############
Downloading py3-zopfli-0.2.3-r2#######################
Downloading py3-zopfli-pyc-0.2.3-r2###################
Downloading qt6-qt3d-6.8.0-r0#########################
Downloading qt6-qt5compat-6.8.0-r0#####################
Downloading qt6-qtbase-6.8.0-r1#########################
Downloading qt6-qtbase-x11-6.8.0-r1#######################
Downloading qt6-qtcharts-6.8.0-r0############################
Downloading qt6-qtconnectivity-6.8.0-r0#######################
Downloading qt6-qtdatavis3d-6.8.0-r0##########################
Downloading qt6-qtdeclarative-6.8.0-r0########################
Downloading qt6-qthttpserver-6.8.0-r0################################
Downloading qt6-qtmultimedia-6.8.0-r0################################
Downloading qt6-qtmultimedia-ffmpeg-6.8.0-r0#########################
Downloading qt6-qtnetworkauth-6.8.0-r0###############################
Downloading qt6-qtpositioning-6.8.0-r0###############################
Downloading qt6-qtquick3d-6.8.0-r0###################################
Downloading qt6-qtquicktimeline-6.8.0-r0################################
Downloading qt6-qtremoteobjects-6.8.0-r0################################
Downloading qt6-qtscxml-6.8.0-r0########################################
Downloading qt6-qtsensors-6.8.0-r0######################################
Downloading qt6-qtserialport-6.8.0-r0###################################
Downloading qt6-qtshadertools-6.8.0-r0##################################
Downloading qt6-qtspeech-6.8.0-r0########################################
Downloading qt6-qtsvg-6.8.0-r0###########################################
Downloading qt6-qttools-libs-6.8.0-r0####################################
Downloading qt6-qtwayland-6.8.0-r1#########################################
Downloading qt6-qtwebchannel-6.8.0-r0#######################################
Downloading qt6-qtwebengine-6.8.0-r0########################################
Downloading qt6-qtwebsockets-libs-6.8.0-r0###############################################################################
Downloading rav1e-libs-0.7.1-r0##########################################################################################
Downloading saphir-gui-0.1-r1############################################################################################
Downloading saphir-lib-0.1-r1###############################################################################################
Downloading shared-mime-info-2.4-r2#########################################################################################
Downloading snappy-1.1.10-r2################################################################################################
Downloading soxr-0.1.3-r7###################################################################################################
Downloading speexdsp-1.2.1-r2###############################################################################################
Downloading tdb-libs-1.4.12-r0##############################################################################################
Downloading tiff-4.7.0-r0###################################################################################################
Downloading tslib-1.23-r0###################################################################################################
Downloading tzdata-2025b-r0#################################################################################################
Downloading util-macros-1.20.1-r0###########################################################################################
Downloading wayland-libs-client-1.23.1-r0###################################################################################
Downloading wayland-libs-cursor-1.23.1-r0###################################################################################
Downloading wayland-libs-egl-1.23.1-r0######################################################################################
Downloading wayland-libs-server-1.23.1-r0###################################################################################
Downloading weasyprint-63.0-r0###############################################################################################
Downloading weasyprint-pyc-63.0-r0###########################################################################################
Downloading x264-libs-0.164.3108-r0##########################################################################################
Downloading x265-libs-3.6-r0#################################################################################################
Downloading xcb-util-0.4.1-r3##################################################################################################
Downloading xcb-util-cursor-0.1.5-r0###########################################################################################
Downloading xcb-util-image-0.4.1-r0############################################################################################
Downloading xcb-util-keysyms-0.4.1-r0##########################################################################################
Downloading xcb-util-renderutil-0.3.10-r0######################################################################################
Downloading xcb-util-wm-0.4.2-r0###############################################################################################
Downloading xdg-utils-1.2.1-r1#################################################################################################
Downloading xe-guest-utilities-8.4.0-r4########################################################################################
Downloading xe-guest-utilities-udev-8.4.0-r4###################################################################################
Downloading xf86-input-libinput-1.5.0-r0#######################################################################################
Downloading xkbcomp-1.4.7-r0###################################################################################################
Downloading xkeyboard-config-2.43-r0###########################################################################################
Downloading xorg-server-21.1.16-r0##############################################################################################
Downloading xorg-server-common-21.1.16-r0#######################################################################################
Downloading xprop-1.2.8-r0######################################################################################################
Downloading xrandr-1.5.2-r0#####################################################################################################
Downloading xset-1.2.5-r1#######################################################################################################
Downloading xsetroot-1.1.3-r1###################################################################################################
Downloading xvidcore-1.3.7-r2###################################################################################################
Downloading zopfli-1.0.3-r3#####################################################################################################
Sign local Alpine repository####################################################################################################

###

total 942744 -> 921 Mo
-rw-r--r--    1 root     root     271520956 Mar 28 22:17 saphir-container-eset-2.0-r1.apk   -> 29,5%
-rw-r--r--    1 root     root     235213131 Dec 30 22:05 saphir-av-clamav-1.0-r1.apk        -> 25,5%
-rw-r--r--    1 root     root     112711752 Nov 29 19:21 qt6-qtwebengine-6.8.0-r0.apk       -> 12,2%
-rw-r--r--    1 root     root      58613139 Mar 27 07:56 llvm19-libs-19.1.4-r1.apk          -> 
-rw-r--r--    1 root     root      32420803 Dec  2 09:50 mesa-24.2.8-r0.apk
-rw-r--r--    1 root     root      21686544 Nov 20 14:47 clang19-libclang-19.1.4-r0.apk
-rw-r--r--    1 root     root      15900880 Nov 29 19:21 py3-pyside6-6.8.0.2-r0.apk
-rw-r--r--    1 root     root      15649881 Nov 29 19:21 qt6-qtdeclarative-6.8.0-r0.apk
-rw-r--r--    1 root     root      13748380 Oct 30 13:34 flite-2.2-r3.apk
-rw-r--r--    1 root     root      12086366 Oct 30 13:34 icu-data-full-74.2-r0.apk
-rw-r--r--    1 root     root      11416250 Feb 23 22:34 clamav-libs-1.4.2-r0.apk
-rw-r--r--    1 root     root      10824030 Feb 23 22:34 clamav-scanner-1.4.2-r0.apk
-rw-r--r--    1 root     root       8912922 Nov 29 19:21 qt6-qtbase-x11-6.8.0-r1.apk
-rw-r--r--    1 root     root       8117782 Apr 10 17:48 python3-3.12.10-r0.apk
-rw-r--r--    1 root     root       7370355 Apr 21 18:20 saphir-gui-0.1-r1.apk
-rw-r--r--    1 root     root       6963264 Dec  9 21:15 ffmpeg-libavcodec-6.1.2-r1.apk
-rw-r--r--    1 root     root       6227954 Nov 29 19:21 qt6-qtquick3d-6.8.0-r0.apk
-rw-r--r--    1 root     root       5693800 Nov 29 19:21 qt6-qtbase-6.8.0-r1.apk
-rw-r--r--    1 root     root       4771972 Nov 29 19:21 qt6-qttools-libs-6.8.0-r0.apk
-rw-r--r--    1 root     root       4669425 Nov 29 19:16 font-roboto-3.005-r0.apk
-rw-r--r--    1 root     root       4161938 Apr 10 17:48 python3-pycache-pyc0-3.12.10-r0.apk
-rw-r--r--    1 root     root       3885701 Mar  7 23:02 gtk+3.0-3.24.49-r0.apk
-rw-r--r--    1 root     root       3687982 Oct 30 13:34 font-misc-misc-1.1.3-r1.apk
-rw-r--r--    1 root     root       3414467 Nov 29 19:24 x265-libs-3.6-r0.apk
-rw-r--r--    1 root     root       3285317 Nov 29 19:21 qt6-qt3d-6.8.0-r0.apk
-rw-r--r--    1 root     root       2960069 Nov 18 22:10 aom-libs-3.11.0-r0.apk
-rw-r--r--    1 root     root       2788764 Nov 29 19:18 libSvtAv1Enc-2.2.1-r0.apk
-rw-r--r--    1 root     root       2364559 Nov 29 19:14 assimp-libs-5.4.3-r0.apk
-rw-r--r--    1 root     root       2223946 Nov 29 19:21 py3-fonttools-4.55.0-r0.apk
-rw-r--r--    1 root     root       2172193 Nov 29 19:21 qt6-qtshadertools-6.8.0-r0.apk
-rw-r--r--    1 root     root       2075972 Nov 29 19:21 py3-pyphen-0.17.0-r0.apk
-rw-r--r--    1 root     root       2024977 Feb 23 21:30 glib-2.82.5-r0.apk
-rw-r--r--    1 root     root       1858574 Nov 29 19:21 py3-fonttools-pyc-4.55.0-r0.apk
-rw-r--r--    1 root     root       1828351 Oct 30 13:34 icu-libs-74.2-r0.apk
-rw-r--r--    1 root     root       1827777 Feb 11 21:23 libcrypto3-3.3.3-r0.apk
-rw-r--r--    1 root     root       1783527 Apr  8 20:52 xe-guest-utilities-8.4.0-r4.apk
-rw-r--r--    1 root     root       1716036 Mar 14 09:40 libjxl-0.10.4-r0.apk
-rw-r--r--    1 root     root       1660547 Mar 17 11:18 nss-3.109-r0.apk
-rw-r--r--    1 root     root       1431586 Nov 29 19:21 py3-shiboken6-6.8.0.2-r0.apk
-rw-r--r--    1 root     root       1344353 Nov 29 19:19 libvpx-1.15.0-r0.apk
-rw-r--r--    1 root     root       1335037 Feb 26 21:09 xorg-server-21.1.16-r0.apk
-rw-r--r--    1 root     root       1321453 Dec  9 21:15 ffmpeg-libavformat-6.1.2-r1.apk
-rw-r--r--    1 root     root       1276203 Dec  1 22:00 qt6-qtwayland-6.8.0-r1.apk
-rw-r--r--    1 root     root        975077 Nov 29 19:21 qt6-qtcharts-6.8.0-r0.apk
-rw-r--r--    1 root     root        967342 Nov 29 19:24 x264-libs-0.164.3108-r0.apk
-rw-r--r--    1 root     root        961810 Nov 20 14:47 clang19-headers-19.1.4-r0.apk
-rw-r--r--    1 root     root        942494 Oct 30 13:34 libstdc++-14.2.0-r4.apk
-rw-r--r--    1 root     root        931285 Nov 12 18:15 gnutls-3.8.8-r0.apk
-rw-r--r--    1 root     root        909600 Nov 29 19:22 rav1e-libs-0.7.1-r0.apk
-rw-r--r--    1 root     root        867164 Oct 30 13:34 libx11-1.8.10-r0.apk
-rw-r--r--    1 root     root        841097 Apr 15 18:39 sqlite-libs-3.48.0-r1.apk
-rw-r--r--    1 root     root        795185 Nov 29 19:21 qt6-qtmultimedia-6.8.0-r0.apk
-rw-r--r--    1 root     root        791936 Dec  2 09:51 sudo-1.9.16_p2-r0.apk
-rw-r--r--    1 root     root        784949 Oct 30 13:34 lxc-6.0.2-r8.apk
-rw-r--r--    1 root     root        725109 Nov 29 19:21 qt6-qtdatavis3d-6.8.0-r0.apk
-rw-r--r--    1 root     root        705487 Oct 30 13:34 libdav1d-1.5.0-r0.apk
-rw-r--r--    1 root     root        659192 Oct 30 13:34 libunistring-1.2-r0.apk
-rw-r--r--    1 root     root        636044 Nov 29 19:21 qt6-qtscxml-6.8.0-r0.apk
-rw-r--r--    1 root     root        606619 Dec  2 22:17 libopenmpt-0.7.12-r0.apk
-rw-r--r--    1 root     root        587136 Oct 30 13:34 encodings-1.0.7-r1.apk
-rw-r--r--    1 root     root        586058 Oct 30 13:34 harfbuzz-9.0.0-r1.apk
-rw-r--r--    1 root     root        574484 Nov 29 19:20 openexr-libopenexrcore-3.3.2-r0.apk
-rw-r--r--    1 root     root        569441 Nov 29 19:19 libpulse-17.0-r4.apk
-rw-r--r--    1 root     root        560704 Nov 29 19:21 qt6-qtconnectivity-6.8.0-r0.apk
-rw-r--r--    1 root     root        559422 Oct 30 13:34 harfbuzz-subset-9.0.0-r1.apk
-rw-r--r--    1 root     root        559354 Nov 29 19:21 py3-pillow-11.0.0-r0.apk
-rw-r--r--    1 root     root        555855 Oct 30 13:35 xkeyboard-config-2.43-r0.apk
-rw-r--r--    1 root     root        552354 Nov 29 19:21 py3-pillow-pyc-11.0.0-r0.apk
-rw-r--r--    1 root     root        527230 Nov 29 19:21 qt6-qt5compat-6.8.0-r0.apk
-rw-r--r--    1 root     root        524867 Nov 29 19:24 weasyprint-pyc-63.0-r0.apk
-rw-r--r--    1 root     root        517227 Oct 30 13:33 cairo-1.18.2-r1.apk
-rw-r--r--    1 root     root        516671 Nov 29 19:21 qt6-qtremoteobjects-6.8.0-r0.apk
-rw-r--r--    1 root     root        512517 Jan  2 09:38 libmagic-5.46-r2.apk
-rw-r--r--    1 root     root        505881 Jan 17 19:15 busybox-1.37.0-r12.apk
-rw-r--r--    1 root     root        495124 Mar 10 23:50 libxml2-2.13.4-r5.apk
-rw-r--r--    1 root     root        482766 Oct 30 13:34 libgcrypt-1.10.3-r1.apk
-rw-r--r--    1 root     root        461610 Oct 30 13:33 alsa-lib-1.2.12-r0.apk
-rw-r--r--    1 root     root        439462 Nov 29 19:20 openexr-libopenexr-3.3.2-r0.apk
-rw-r--r--    1 root     root        419817 Oct 30 13:35 py3-brotli-1.1.0-r2.apk
-rw-r--r--    1 root     root        416346 Nov 29 19:21 qt6-qtpositioning-6.8.0-r0.apk
-rw-r--r--    1 root     root        414536 Oct 30 13:33 brotli-libs-1.1.0-r2.apk
-rw-r--r--    1 root     root        411323 Feb 13 18:58 musl-1.2.5-r9.apk
-rw-r--r--    1 root     root        410730 Nov 29 19:19 libsrt-1.5.3-r0.apk
-rw-r--r--    1 root     root        410468 Apr  4 01:56 mbedtls-3.6.3-r0.apk
-rw-r--r--    1 root     root        407653 Dec  9 21:15 ffmpeg-libavutil-6.1.2-r1.apk
-rw-r--r--    1 root     root        383089 Oct 30 13:34 lxc-libs-6.0.2-r8.apk
-rw-r--r--    1 root     root        375122 Dec 25 08:27 zstd-libs-1.5.6-r2.apk
-rw-r--r--    1 root     root        370198 Jan  1 17:47 shared-mime-info-2.4-r2.apk
-rw-r--r--    1 root     root        364845 Oct 30 13:35 p11-kit-0.25.5-r2.apk
-rw-r--r--    1 root     root        357457 Feb 11 21:23 libssl3-3.3.3-r0.apk
-rw-r--r--    1 root     root        348724 Oct 30 13:34 freetype-2.13.3-r0.apk
-rw-r--r--    1 root     root        344873 Mar  7 03:39 hwdata-pci-0.393-r0.apk
-rw-r--r--    1 root     root        343060 Oct 30 13:35 nettle-3.10-r1.apk
-rw-r--r--    1 root     root        328656 Oct 30 13:34 libtheora-1.1.1-r18.apk
-rw-r--r--    1 root     root        310940 Mar 17 10:43 libcurl-8.12.1-r1.apk
-rw-r--r--    1 root     root        302744 Nov 29 19:16 duktape-2.7.0-r1.apk
-rw-r--r--    1 root     root        286504 Oct 30 13:35 pcre2-10.43-r0.apk
-rw-r--r--    1 root     root        283004 Oct 30 13:34 libevent-2.1.12-r7.apk
-rw-r--r--    1 root     root        279966 Nov 29 19:24 weasyprint-63.0-r0.apk
-rw-r--r--    1 root     root        269723 Mar 14 00:14 py3-jinja2-pyc-3.1.6-r0.apk
-rw-r--r--    1 root     root        262630 Oct 30 13:34 libzmq-4.3.5-r2.apk
-rw-r--r--    1 root     root        262463 Oct 30 13:34 eudev-3.2.14-r5.apk
-rw-r--r--    1 root     root        260820 Oct 30 13:34 libpcre2-16-10.43-r0.apk
-rw-r--r--    1 root     root        256970 Oct 30 13:35 pango-1.54.0-r1.apk
-rw-r--r--    1 root     root        256304 Nov 29 19:21 qt6-qtsvg-6.8.0-r0.apk
-rw-r--r--    1 root     root        246847 Oct 30 13:34 libwebp-1.4.0-r0.apk
-rw-r--r--    1 root     root        246106 Oct 30 13:35 pixman-0.43.4-r1.apk
-rw-r--r--    1 root     root        245775 Oct 30 13:35 opus-1.5.2-r1.apk
-rw-r--r--    1 root     root        242751 Nov 29 19:18 libimagequant-4.2.2-r0.apk
-rw-r--r--    1 root     root        238665 Oct 30 13:34 libxcb-1.16.1-r0.apk
-rw-r--r--    1 root     root        236454 Oct 30 13:34 libepoxy-1.5.10-r1.apk
-rw-r--r--    1 root     root        235322 Oct 30 13:34 cups-libs-2.4.11-r0.apk
-rw-r--r--    1 root     root        227542 Jan  1 13:15 libsndfile-1.2.2-r2.apk
-rw-r--r--    1 root     root        225128 Oct 30 13:34 libjpeg-turbo-3.0.4-r0.apk
-rw-r--r--    1 root     root        223607 Nov 29 19:21 qt6-qtmultimedia-ffmpeg-6.8.0-r0.apk
-rw-r--r--    1 root     root        221446 Oct 30 13:34 gmp-6.3.0-r2.apk
-rw-r--r--    1 root     root        206455 Dec  2 09:50 mesa-gl-24.2.8-r0.apk
-rw-r--r--    1 root     root        202489 Nov 29 19:21 qt6-qtsensors-6.8.0-r0.apk
-rw-r--r--    1 root     root        202265 Oct 30 13:34 libflac-1.4.3-r1.apk
-rw-r--r--    1 root     root        197862 Dec  1 13:13 openxr-1.1.43-r0.apk
-rw-r--r--    1 root     root        197526 Oct 30 13:34 libdrm-2.4.123-r1.apk
-rw-r--r--    1 root     root        196679 Oct 30 13:35 orc-0.4.40-r1.apk
-rw-r--r--    1 root     root        187021 Mar 25 11:04 tzdata-2025b-r0.apk
-rw-r--r--    1 root     root        186903 Dec  9 21:15 ffmpeg-libswscale-6.1.2-r1.apk
-rw-r--r--    1 root     root        185775 Nov 29 19:19 libssh-0.11.1-r0.apk
-rw-r--r--    1 root     root        183860 Oct 30 13:34 libvorbis-1.3.7-r2.apk
-rw-r--r--    1 root     root        175491 Oct 30 13:35 py3-cparser-pyc-2.22-r1.apk
-rw-r--r--    1 root     root        173924 Nov 29 19:21 py3-psutil-pyc-6.0.0-r0.apk
-rw-r--r--    1 root     root        173601 Oct 30 13:35 py3-cffi-pyc-1.17.1-r1.apk
-rw-r--r--    1 root     root        172299 Nov  5 17:45 mpg123-libs-1.32.9-r0.apk
-rw-r--r--    1 root     root        168870 Oct 30 13:34 libsodium-1.0.20-r0.apk
-rw-r--r--    1 root     root        165017 Oct 30 13:35 tiff-4.7.0-r0.apk
-rw-r--r--    1 root     root        161819 Oct 30 13:34 fontconfig-2.15.0-r1.apk
-rw-r--r--    1 root     root        161737 Oct 30 13:35 py3-cffi-1.17.1-r1.apk
-rw-r--r--    1 root     root        159283 Nov 29 19:18 libbluray-1.3.4-r1.apk
-rw-r--r--    1 root     root        158593 Nov 11 18:11 libncursesw-6.5_p20241006-r3.apk
-rw-r--r--    1 root     root        153983 Nov 26 15:48 libxt-1.3.1-r0.apk
-rw-r--r--    1 root     root        151664 Oct 30 13:34 lcms2-2.16-r0.apk
-rw-r--r--    1 root     root        149473 Oct 30 13:34 libgomp-14.2.0-r4.apk
-rw-r--r--    1 root     root        148745 Feb 23 22:34 clamav-daemon-1.4.2-r0.apk
-rw-r--r--    1 root     root        148268 Nov 29 19:25 xvidcore-1.3.7-r2.apk
-rw-r--r--    1 root     root        147221 Oct 30 13:34 gdk-pixbuf-2.42.12-r1.apk
-rw-r--r--    1 root     root        146427 Apr 21 17:52 psec-lib-1.1-r0.apk
-rw-r--r--    1 root     root        142821 Nov 29 19:21 py3-pyserial-pyc-3.5-r7.apk
-rw-r--r--    1 root     root        138475 Mar 14 16:56 libxslt-1.1.42-r2.apk
-rw-r--r--    1 root     root        135202 Oct 30 13:35 openjpeg-2.5.2-r0.apk
-rw-r--r--    1 root     root        133258 Jan 13 22:30 at-spi2-core-2.54.1-r0.apk
-rw-r--r--    1 root     root        131206 Dec  2 09:50 mesa-egl-24.2.8-r0.apk
-rw-r--r--    1 root     root        130932 Jan  8 10:58 ca-certificates-bundle-20241121-r1.apk
-rw-r--r--    1 root     root        130579 Oct 30 13:34 libxkbcommon-1.7.0-r1.apk
-rw-r--r--    1 root     root        128668 Mar 14 00:14 py3-jinja2-3.1.6-r0.apk
-rw-r--r--    1 root     root        128371 Nov 29 19:21 qt6-qtspeech-6.8.0-r0.apk
-rw-r--r--    1 root     root        127194 Nov 29 19:18 libinput-libs-1.27.0-r0.apk
-rw-r--r--    1 root     root        126201 Nov 29 19:21 qt6-qtwebchannel-6.8.0-r0.apk
-rw-r--r--    1 root     root        125263 Nov 25 17:09 nspr-4.36-r0.apk
-rw-r--r--    1 root     root        124379 Oct 30 13:34 dbus-libs-1.14.10-r4.apk
-rw-r--r--    1 root     root        124190 Oct 30 13:34 lame-libs-3.100-r5.apk
-rw-r--r--    1 root     root        123214 Apr 16 10:18 libmount-2.40.4-r1.apk
-rw-r--r--    1 root     root        120509 Oct 30 13:35 readline-8.2.13-r0.apk
-rw-r--r--    1 root     root        116437 Apr  4 23:47 xz-libs-5.6.3-r1.apk
-rw-r--r--    1 root     root        113019 Oct 30 13:35 py3-cparser-2.22-r1.apk
-rw-r--r--    1 root     root        112460 Nov 29 19:21 py3-psutil-6.0.0-r0.apk
-rw-r--r--    1 root     root        111679 Nov 29 19:25 zopfli-1.0.3-r3.apk
-rw-r--r--    1 root     root        110189 Nov 29 19:20 openexr-libiex-3.3.2-r0.apk
-rw-r--r--    1 root     root        108059 Nov 29 19:20 onevpl-libs-2023.3.1-r2.apk
-rw-r--r--    1 root     root        107448 Apr  9 22:55 c-ares-1.34.5-r0.apk
-rw-r--r--    1 root     root        105492 Mar 28 21:10 py3-paho-mqtt2-pyc-2.1.0-r3.apk
-rw-r--r--    1 root     root        104380 Oct 30 13:34 libidn2-2.3.7-r0.apk
-rw-r--r--    1 root     root        103320 Feb 23 22:34 clamav-1.4.2-r0.apk
-rw-r--r--    1 root     root        101622 Nov 29 19:19 libxfont2-2.0.7-r0.apk
-rw-r--r--    1 root     root         95717 Mar 17 11:18 libpng-1.6.47-r0.apk
-rw-r--r--    1 root     root         94106 Apr 16 10:18 libblkid-2.40.4-r1.apk
-rw-r--r--    1 root     root         88276 Nov 29 19:24 tslib-1.23-r0.apk
-rw-r--r--    1 root     root         87365 Nov 29 19:17 imath-3.1.12-r0.apk
-rw-r--r--    1 root     root         82190 Nov 29 19:21 py3-tinyhtml5-pyc-2.0.0-r0.apk
-rw-r--r--    1 root     root         81487 Oct 30 13:34 libgcc-14.2.0-r4.apk
-rw-r--r--    1 root     root         81179 Oct 30 13:34 libva-2.22.0-r1.apk
-rw-r--r--    1 root     root         80580 Nov 29 19:21 qt6-qtnetworkauth-6.8.0-r0.apk
-rw-r--r--    1 root     root         80223 Oct 30 13:35 xkbcomp-1.4.7-r0.apk
-rw-r--r--    1 root     root         76258 Nov 29 19:21 qt6-qtwebsockets-libs-6.8.0-r0.apk
-rw-r--r--    1 root     root         75913 Nov 29 19:21 py3-pyserial-3.5-r7.apk
-rw-r--r--    1 root     root         75070 Oct 30 13:35 mpdecimal-4.0.0-r0.apk
-rw-r--r--    1 root     root         74829 Nov 29 19:21 qt6-qthttpserver-6.8.0-r0.apk
-rw-r--r--    1 root     root         74143 Nov 29 19:22 soxr-0.1.3-r7.apk
-rw-r--r--    1 root     root         72530 Nov 29 19:24 xdg-utils-1.2.1-r1.apk
-rw-r--r--    1 root     root         71168 Nov 19 08:25 libgpg-error-1.51-r0.apk
-rw-r--r--    1 root     root         70881 Jan 13 22:30 libatk-1.0-2.54.1-r0.apk
-rw-r--r--    1 root     root         70431 Nov  6 01:08 bluez-libs-5.79-r0.apk
-rw-r--r--    1 root     root         68722 Nov 29 19:21 py3-msgpack-1.0.8-r1.apk
-rw-r--r--    1 root     root         68483 Nov 29 19:21 qt6-qtquicktimeline-6.8.0-r0.apk
-rw-r--r--    1 root     root         68096 Nov 29 19:19 librist-0.2.10-r1.apk
-rw-r--r--    1 root     root         67341 Jan 13 22:30 libatk-bridge-2.0-2.54.1-r0.apk
-rw-r--r--    1 root     root         66433 Nov  5 17:45 nghttp2-libs-1.64.0-r0.apk
-rw-r--r--    1 root     root         63504 Oct 30 13:34 graphite2-1.3.14-r6.apk
-rw-r--r--    1 root     root         63464 Mar 28 21:10 py3-paho-mqtt2-2.1.0-r3.apk
-rw-r--r--    1 root     root         61345 Nov 29 19:18 libdeflate-1.22-r0.apk
-rw-r--r--    1 root     root         60438 Dec  8 17:56 py3-udev-pyc-0.24.1-r2.apk
-rw-r--r--    1 root     root         58729 Oct 30 13:34 libxkbfile-1.1.3-r0.apk
-rw-r--r--    1 root     root         58271 Mar 16 23:37 libexpat-2.7.0-r0.apk
-rw-r--r--    1 root     root         54649 Oct 30 13:34 libpsl-0.21.5-r3.apk
-rw-r--r--    1 root     root         53979 Oct 30 13:35 zlib-1.3.1-r2.apk
-rw-r--r--    1 root     root         50694 Dec  9 21:15 ffmpeg-libswresample-6.1.2-r1.apk
-rw-r--r--    1 root     root         49880 Oct 30 13:35 pkgconf-2.3.0-r0.apk
-rw-r--r--    1 root     root         48789 Nov 29 19:18 libb2-0.98.1-r3.apk
-rw-r--r--    1 root     root         47374 Dec  2 09:50 mesa-glapi-24.2.8-r0.apk
-rw-r--r--    1 root     root         47090 Oct 30 13:34 libxmu-1.2.1-r0.apk
-rw-r--r--    1 root     root         46788 Nov 29 19:21 py3-humanize-4.9.0-r1.apk
-rw-r--r--    1 root     root         46570 Nov 29 19:21 py3-evdev-1.7.1-r0.apk
-rw-r--r--    1 root     root         46427 Oct 30 13:34 libseccomp-2.5.5-r1.apk
-rw-r--r--    1 root     root         45328 Nov 29 19:21 qt6-qtserialport-6.8.0-r0.apk
-rw-r--r--    1 root     root         43948 Apr 21 19:59 APKINDEX.tar.gz
-rw-r--r--    1 root     root         43473 Oct 30 13:34 libelf-0.191-r0.apk
-rw-r--r--    1 root     root         42571 Feb 23 22:34 clamav-clamdscan-1.4.2-r0.apk
-rw-r--r--    1 root     root         42290 Oct 30 13:33 avahi-libs-0.8-r19.apk
-rw-r--r--    1 root     root         42217 Nov 29 19:21 py3-tinycss2-pyc-1.4.0-r0.apk
-rw-r--r--    1 root     root         40610 Nov 25 17:36 tdb-libs-1.4.12-r0.apk
-rw-r--r--    1 root     root         39832 Oct 30 13:34 kmod-libs-33-r2.apk
-rw-r--r--    1 root     root         39700 Nov 29 19:21 py3-tinyhtml5-2.0.0-r0.apk
-rw-r--r--    1 root     root         39519 Nov 29 19:16 double-conversion-3.3.0-r0.apk
-rw-r--r--    1 root     root         39164 Oct 30 13:34 libice-1.1.1-r6.apk
-rw-r--r--    1 root     root         38315 Oct 30 13:34 libxft-2.3.8-r3.apk
-rw-r--r--    1 root     root         37753 Dec  8 17:56 py3-udev-0.24.1-r2.apk
-rw-r--r--    1 root     root         35532 Nov 29 19:21 py3-evdev-pyc-1.7.1-r0.apk
-rw-r--r--    1 root     root         34871 Oct 30 13:35 speexdsp-1.2.1-r2.apk
-rw-r--r--    1 root     root         33347 Feb  7 21:59 libtasn1-4.20.0-r0.apk
-rw-r--r--    1 root     root         32791 Oct 30 13:34 libbz2-1.0.8-r6.apk
-rw-r--r--    1 root     root         32566 Nov 29 19:18 libmspack-0.11_alpha-r1.apk
-rw-r--r--    1 root     root         31789 Nov 29 19:24 xf86-input-libinput-1.5.0-r0.apk
-rw-r--r--    1 root     root         31093 Oct 30 13:34 libintl-0.22.5-r0.apk
-rw-r--r--    1 root     root         30998 Oct 30 13:34 gdbm-1.24-r0.apk
-rw-r--r--    1 root     root         30417 Oct 30 13:34 libbsd-0.12.2-r0.apk
-rw-r--r--    1 root     root         29688 Oct 30 13:35 wayland-libs-server-1.23.1-r0.apk
-rw-r--r--    1 root     root         28441 Dec  2 09:50 mesa-gbm-24.2.8-r0.apk
-rw-r--r--    1 root     root         28221 Oct 30 13:34 fribidi-1.0.16-r0.apk
-rw-r--r--    1 root     root         28076 Oct 30 13:34 json-c-0.18-r0.apk
-rw-r--r--    1 root     root         27877 Nov 29 19:21 py3-cssselect2-pyc-0.7.0-r5.apk
-rw-r--r--    1 root     root         27579 Oct 30 13:34 hicolor-icon-theme-0.18-r0.apk
-rw-r--r--    1 root     root         27565 Feb 23 22:34 freshclam-1.4.2-r0.apk
-rw-r--r--    1 root     root         27337 Oct 30 13:34 libxi-1.8.2-r0.apk
-rw-r--r--    1 root     root         27273 Nov 29 19:18 libevdev-1.13.3-r0.apk
-rw-r--r--    1 root     root         26419 Oct 30 13:34 eudev-libs-3.2.14-r5.apk
-rw-r--r--    1 root     root         26335 Oct 30 13:34 libvdpau-1.5-r4.apk
-rw-r--r--    1 root     root         26034 Nov 29 19:25 xrandr-1.5.2-r0.apk
-rw-r--r--    1 root     root         25228 Oct 30 13:34 libxext-1.3.6-r2.apk
-rw-r--r--    1 root     root         24928 Nov 29 19:21 py3-tinycss2-1.4.0-r0.apk
-rw-r--r--    1 root     root         24849 Oct 30 13:35 util-macros-1.20.1-r0.apk
-rw-r--r--    1 root     root         24380 Oct 30 13:34 libeconf-0.6.3-r0.apk
-rw-r--r--    1 root     root         23076 Oct 30 13:34 libmd-1.1.0-r0.apk
-rw-r--r--    1 root     root         22670 Nov 29 19:21 py3-humanize-pyc-4.9.0-r1.apk
-rw-r--r--    1 root     root         21902 Nov 18 22:10 libcap2-2.71-r0.apk
-rw-r--r--    1 root     root         21781 Oct 30 13:35 snappy-1.1.10-r2.apk
-rw-r--r--    1 root     root         21579 Nov 29 19:21 py3-msgpack-pyc-1.0.8-r1.apk
-rw-r--r--    1 root     root         21379 Oct 30 13:35 wayland-libs-client-1.23.1-r0.apk
-rw-r--r--    1 root     root         21319 Nov 11 18:11 ncurses-terminfo-base-6.5_p20241006-r3.apk
-rw-r--r--    1 root     root         21013 Oct 30 13:34 libwebpmux-1.4.0-r0.apk
-rw-r--r--    1 root     root         20949 Nov 29 19:24 xcb-util-wm-0.4.2-r0.apk
-rw-r--r--    1 root     root         20660 Nov 29 19:19 libproxy-0.5.9-r0.apk
-rw-r--r--    1 root     root         20446 Oct 30 13:34 libogg-1.3.5-r5.apk
-rw-r--r--    1 root     root         19933 Oct 30 13:35 numactl-2.0.18-r0.apk
-rw-r--r--    1 root     root         19592 Nov 29 19:18 libhwy-1.0.7-r0.apk
-rw-r--r--    1 root     root         19179 Dec  2 09:50 mesa-dri-gallium-24.2.8-r0.apk
-rw-r--r--    1 root     root         18648 Nov 19 08:25 libxcursor-1.2.3-r0.apk
-rw-r--r--    1 root     root         18238 Apr 21 17:56 saphir-lib-0.1-r1.apk
-rw-r--r--    1 root     root         18112 Feb 28 18:43 libffi-3.4.7-r0.apk
-rw-r--r--    1 root     root         17325 Nov 29 19:19 minizip-1.3.1-r0.apk
-rw-r--r--    1 root     root         17111 Dec  4 11:30 xprop-1.2.8-r0.apk
-rw-r--r--    1 root     root         16560 Oct 30 13:34 libltdl-2.4.7-r3.apk
-rw-r--r--    1 root     root         16063 Oct 30 13:34 libxrender-0.9.11-r5.apk
-rw-r--r--    1 root     root         16010 Oct 30 13:35 py3-webencodings-pyc-0.5.1-r8.apk
-rw-r--r--    1 root     root         15953 Oct 30 13:34 libxrandr-1.5.4-r1.apk
-rw-r--r--    1 root     root         15841 Nov 29 19:21 py3-cssselect2-0.7.0-r5.apk
-rw-r--r--    1 root     root         15580 Apr  9 10:33 giflib-5.2.2-r1.apk
-rw-r--r--    1 root     root         15383 Oct 30 13:35 mkfontscale-1.2.3-r1.apk
-rw-r--r--    1 root     root         14965 Nov 29 19:21 py3-zopfli-0.2.3-r2.apk
-rw-r--r--    1 root     root         14525 Mar  7 23:02 gtk-update-icon-cache-3.24.49-r0.apk
-rw-r--r--    1 root     root         14460 Oct 30 13:34 libpciaccess-0.18.1-r0.apk
-rw-r--r--    1 root     root         14288 Nov 29 19:20 openexr-libilmthread-3.3.2-r0.apk
-rw-r--r--    1 root     root         14264 Oct 30 13:34 libsm-1.2.4-r4.apk
-rw-r--r--    1 root     root         14219 Nov 29 19:21 py3-pydyf-pyc-0.11.0-r0.apk
-rw-r--r--    1 root     root         13952 Apr 16 10:18 libuuid-2.40.4-r1.apk
-rw-r--r--    1 root     root         13090 Oct 30 13:34 libxkbcommon-x11-1.7.0-r1.apk
-rw-r--r--    1 root     root         12849 Oct 30 13:33 cjson-1.7.18-r0.apk
-rw-r--r--    1 root     root         12323 Oct 30 13:34 libsharpyuv-1.4.0-r0.apk
-rw-r--r--    1 root     root         12000 Nov 29 19:25 xset-1.2.5-r1.apk
-rw-r--r--    1 root     root         11439 Oct 30 13:34 libfontenc-1.1.8-r0.apk
-rw-r--r--    1 root     root         11300 Oct 30 13:35 py3-markupsafe-3.0.2-r0.apk
-rw-r--r--    1 root     root         10126 Oct 30 13:35 py3-markupsafe-pyc-3.0.2-r0.apk
-rw-r--r--    1 root     root         10121 Oct 30 13:35 py3-webencodings-0.5.1-r8.apk
-rw-r--r--    1 root     root          9866 Nov 29 19:18 libasyncns-0.8-r4.apk
-rw-r--r--    1 root     root          9836 Oct 30 13:34 libxtst-1.2.5-r0.apk
-rw-r--r--    1 root     root          9663 Jan  2 09:38 file-5.46-r2.apk
-rw-r--r--    1 root     root          9440 Nov 29 19:19 mtdev-1.1.7-r0.apk
-rw-r--r--    1 root     root          9377 Oct 30 13:34 libxdmcp-1.1.5-r1.apk
-rw-r--r--    1 root     root          9363 Nov 29 19:21 py3-pydyf-0.11.0-r0.apk
-rw-r--r--    1 root     root          9337 Oct 30 13:34 libwebpdemux-1.4.0-r0.apk
-rw-r--r--    1 root     root          9243 Oct 30 13:33 cairo-gobject-1.18.2-r1.apk
-rw-r--r--    1 root     root          8922 Oct 30 13:35 wayland-libs-cursor-1.23.1-r0.apk
-rw-r--r--    1 root     root          8533 Oct 30 13:34 libxfixes-6.0.1-r4.apk
-rw-r--r--    1 root     root          8507 Nov 29 19:21 py3-pyphen-pyc-0.17.0-r0.apk
-rw-r--r--    1 root     root          8426 Feb 26 21:09 xorg-server-common-21.1.16-r0.apk
-rw-r--r--    1 root     root          8286 Dec  2 09:51 xcb-util-cursor-0.1.5-r0.apk
-rw-r--r--    1 root     root          8124 Nov 29 19:24 xcb-util-image-0.4.1-r0.apk
-rw-r--r--    1 root     root          7563 Oct 30 13:34 libxxf86vm-1.1.5-r6.apk
-rw-r--r--    1 root     root          7528 Oct 30 13:35 musl-fts-1.2.7-r6.apk
-rw-r--r--    1 root     root          7429 Nov 29 19:25 xsetroot-1.1.3-r1.apk
-rw-r--r--    1 root     root          7400 Nov 29 19:18 libinput-udev-1.27.0-r0.apk
-rw-r--r--    1 root     root          7328 Oct 30 13:35 xcb-util-0.4.1-r3.apk
-rw-r--r--    1 root     root          6952 Oct 30 13:34 font-cursor-misc-1.0.4-r1.apk
-rw-r--r--    1 root     root          6901 Nov 29 19:19 libxcvt-0.1.2-r0.apk
-rw-r--r--    1 root     root          6605 Nov 29 19:21 py3-zopfli-pyc-0.2.3-r2.apk
-rw-r--r--    1 root     root          6164 Nov 29 19:24 xcb-util-renderutil-0.3.10-r0.apk
-rw-r--r--    1 root     root          5594 Nov 11 18:11 libpanelw-6.5_p20241006-r3.apk
-rw-r--r--    1 root     root          5561 Oct 30 13:34 libxau-1.0.11-r4.apk
-rw-r--r--    1 root     root          4896 Nov 29 19:24 xcb-util-keysyms-0.4.1-r0.apk
-rw-r--r--    1 root     root          4841 Oct 30 13:34 libxdamage-1.1.6-r5.apk
-rw-r--r--    1 root     root          4805 Oct 30 13:35 udev-init-scripts-openrc-35-r1.apk
-rw-r--r--    1 root     root          4730 Oct 30 13:34 libxcomposite-0.4.6-r5.apk
-rw-r--r--    1 root     root          4635 Jan 17 19:15 ssl_client-1.37.0-r12.apk
-rw-r--r--    1 root     root          4497 Oct 30 13:34 libxinerama-1.1.5-r4.apk
-rw-r--r--    1 root     root          4066 Apr 21 17:50 psec-gui-base-1.0-r1.apk
-rw-r--r--    1 root     root          3886 Oct 30 13:34 font-alias-1.0.5-r0.apk
-rw-r--r--    1 root     root          3728 Oct 30 13:34 libxshmfence-1.3.2-r6.apk
-rw-r--r--    1 root     root          3541 Apr  2 10:36 psec-sys-usb-1.0-r5.apk
-rw-r--r--    1 root     root          3264 Oct 30 13:35 wayland-libs-egl-1.23.1-r0.apk
-rw-r--r--    1 root     root          2688 Oct 30 13:35 py3-brotli-pyc-1.1.0-r2.apk
-rw-r--r--    1 root     root          2619 Apr 21 17:53 saphir-av-eset-1.0-r1.apk
-rw-r--r--    1 root     root          2165 Oct 30 13:34 eudev-openrc-3.2.14-r5.apk
-rw-r--r--    1 root     root          2121 Oct 30 13:34 libtirpc-conf-1.3.5-r0.apk
-rw-r--r--    1 root     root          1718 Apr  8 20:52 xe-guest-utilities-udev-8.4.0-r4.apk
-rw-r--r--    1 root     root          1688 Oct 30 13:34 krb5-conf-1.0-r2.apk
-rw-r--r--    1 root     root          1509 Jan 17 19:15 busybox-binsh-1.37.0-r12.apk
-rw-r--r--    1 root     root          1256 Apr 10 17:48 python3-pyc-3.12.10-r0.apk
-rw-r--r--    1 root     root          1239 Oct 30 13:35 udev-init-scripts-35-r1.apk
-rw-r--r--    1 root     root          1212 Apr 10 17:48 pyc-3.12.10-r0.apk