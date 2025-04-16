#!/bin/sh

lxc-attach -n saphir-container-eset -- /opt/eset/eea/bin/odscan --version | awk '{print $NF}'