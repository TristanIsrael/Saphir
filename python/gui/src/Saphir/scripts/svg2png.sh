#!/bin/bash

# Répertoire racine, par défaut le dossier courant
ROOT_DIR="${1:-.}"

# DPI cible
DPI=96

# Trouver tous les fichiers .svg de façon récursive
find "$ROOT_DIR" -type f -name "*.svg" | while read -r svg_file; do
    # Nom sans extension
    base_name=$(basename "$svg_file" .svg)

    # Répertoire du fichier d'origine
    dir_name=$(dirname "$svg_file")

    # Fichier de sortie
    output_file="$dir_name/$base_name.png"

    echo "Conversion de : $svg_file -> $output_file"

    # Conversion
    rsvg-convert -d "$DPI" -p "$DPI" "$svg_file" -o "$output_file"
done

echo "Conversion terminée."
