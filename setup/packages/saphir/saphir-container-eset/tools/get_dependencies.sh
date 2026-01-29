#!/bin/sh

LIST_FILE="$1"
ROOTFS_SRC="$2"
ROOTFS_MIN="$3"

if [ -z "$LIST_FILE" ] || [ -z "$ROOTFS_SRC" ] || [ -z "$ROOTFS_MIN" ]; then
    echo "Usage: $0 <used files.txt> <original rootfs> <target rootfs>"
    exit 1
fi

# Résolution des chemins absolus
LIST_FILE="$(realpath "$LIST_FILE")"
ROOTFS_SRC="$(realpath "$ROOTFS_SRC")"
ROOTFS_MIN="$(realpath "$ROOTFS_MIN")"

QUEUE="$(mktemp)"
SEEN="$(mktemp)"

sort -u "$LIST_FILE" > "$QUEUE"

is_elf() {
    localpath="${1#$ROOTFS_SRC}"
    #lxc-attach -n saphir-container-eset -- file -b "$1" 2>/dev/null | grep -q 'ELF'
    lxc-attach -n saphir-container-eset -- head -c 4 "$localpath" 2>/dev/null  | grep -q "\x7fELF"
}

get_ldd_deps() {
    localpath="${1#$ROOTFS_SRC}"
    #echo "Look for dependencies of $localpath"
    lxc-attach -n saphir-container-eset -- ldd "$localpath" 2>/dev/null | awk '{print $3}' | grep '^/'    
}

resolve_symlink() {
    localpath="${1#$ROOTFS_SRC}"
    lxc-attach -n saphir-container-eset -- sh -c "
        SRC='$localpath'
        # Résoudre le lien si c'est un symlink
        if [ -L \"\$SRC\" ]; then
            TARGET=\$(readlink \"\$SRC\")
            case \"\$TARGET\" in
                /*) SRC=\"\$TARGET\" ;;
                *)  SRC=\$(dirname \"\$SRC\")/\$TARGET ;;
            esac
            echo \"\$SRC\"
        else
            echo "$localpath"
        fi        
    "
    #local p="$1"
    #if [ -L "$p" ]; then
    #    target="$(readlink "$p")"
    #    case "$target" in
    #        /*) echo "$target" ;;
    #        *)  echo "$(dirname "$p")/$target" ;;
    #    esac
    #else
    #    echo "$p"
    #fi
}

while read -r path; do
    echo "$path" >> "$SEEN"

    SRC="$(resolve_symlink "$ROOTFS_SRC$path")"
    DST="$ROOTFS_MIN$path"

    #echo "$SRC -> $DST"
    #copy_entry "$SRC" "$DST"

    # Si ELF → récupérer dépendances
    if is_elf "$SRC"; then
        get_ldd_deps "$SRC" | while read -r dep; do
            if ! grep -qx "$dep" "$SEEN"; then
                echo "$dep"
                echo "$dep" >> "$QUEUE"
            fi
        done
    fi

done < "$QUEUE"

rm $SEEN
rm $QUEUE