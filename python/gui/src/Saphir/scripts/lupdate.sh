#!/bin/sh

if [ $# -ne 2 ]; then
    echo "Missing arguments"
    echo "Usage: $0 <source_dir> <ts_filename>"
    exit 1
fi

cd $1

echo "Update the translations file $2"
pyside6-lupdate main.py Saphir/*.py GUI/Components/*.qml GUI/content/*.qml -ts $2
echo "Done"

cd -
