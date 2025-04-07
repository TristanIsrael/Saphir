#!/bin/sh

lxc-attach -n saphir-container-eset -- /opt/eset/eea/bin/odscan -s --profile="@In-depth scan" --show-scan-info $1