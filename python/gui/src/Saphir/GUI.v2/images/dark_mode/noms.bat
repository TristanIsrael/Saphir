@echo off
setlocal

REM Récupération du nom du répertoire
set "repertoire=%cd%"

REM Création du fichier texte
set "fichier=%repertoire%\liste_fichiers.txt"

REM Création du fichier texte
echo. > "%fichier%"

REM Récupération des noms des fichiers
for %%f in (*) do (
    echo %%f >> "%fichier%"
)

echo Fichiers récupérés avec succès.
endlocal
