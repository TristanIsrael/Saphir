#!/bin/sh

lxc-attach -n saphir-container-eset -- /opt/eset/eea/sbin/lic -s
