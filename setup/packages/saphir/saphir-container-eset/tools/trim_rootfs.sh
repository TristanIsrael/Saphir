#!/bin/bash
# Usage: ./trim_rootfs.sh <liste_fichiers_utilises.txt> <rootfs_original> <rootfs_min_destination>

set -e

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

echo Files list: $LIST_FILE
echo Original rootfs: $ROOTFS_SRC
echo Target rootfs: $ROOTFS_MIN

mkdir -p "$ROOTFS_MIN"

copy_entry() {
  SRC="$1"
  DST="$2"

  [ -L "$SRC" ] || [ -e "$SRC" ] || return 0

  mkdir -p "$(dirname "$DST")"

  if [ -L "$SRC" ]; then
    echo Copy link $SRC
    TARGET="$(readlink "$SRC")"
    ln -s "$TARGET" "$DST" || true

    # copier la cible du lien
    case "$TARGET" in
      /*) REAL="$ROOTFS_SRC$TARGET" ;;
      *)  REAL="$(dirname "$SRC")/$TARGET" ;;
    esac

    copy_entry "$REAL" "$ROOTFS_MIN${REAL#$ROOTFS_SRC}"
  elif [ -d "$SRC" ]; then
    echo Create dir $SRC
    mkdir -p "$DST"
  else
    echo Copy file $SRC
    cp -p "$SRC" "$DST"
  fi
}

while IFS= read -r path; do
  SRC="$ROOTFS_SRC$path"
  DST="$ROOTFS_MIN$path"
  copy_entry "$SRC" "$DST"
done < "$LIST_FILE"

# Add required files
#cp -ar $ROOTFS_SRC/lib/systemd $ROOTFS_MIN/lib/
#cp -ar $ROOTFS_SRC/lib/x86_64-linux-gnu/systemd $ROOTFS_MIN/lib/x86_64-linux-gnu/
#cp -ar $ROOTFS_SRC/sbin/init $ROOTFS_MIN/sbin
cp -ar $ROOTFS_SRC/lib64 $ROOTFS_MIN/
cp -ar $ROOTFS_SRC/usr/lib64 $ROOTFS_MIN/usr/
cp -ar $ROOTFS_SRC/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 $ROOTFS_MIN/lib/x86_64-linux-gnu/

echo "✅ Rootfs constructed in $ROOTFS_MIN"