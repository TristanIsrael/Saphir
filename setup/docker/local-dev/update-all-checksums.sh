#!/bin/sh

PACKAGES="saphir saphir-av-clamav saphir-av-eset saphir-container-eset saphir-gui saphir-lib saphir-splash"
for pkg in $PACKAGES; do
    ./docker-cmd.sh 'cd /home/builder/src/Saphir/setup/packages/saphir/'$pkg' && abuild checksum && abuild clean'
done