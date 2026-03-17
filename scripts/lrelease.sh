#!/bin/sh

if [ $# -ne 1 ]; then
    echo "Missing arguments"
    echo "Usage: $0 <ts_filepath>"
    exit 1
fi

QM_FILE="${1%.*}.qm"

echo "Compile the translations in the file $QM_FILE"

pyside6-lrelease $1 -qm $QM_FILE

echo "Done"