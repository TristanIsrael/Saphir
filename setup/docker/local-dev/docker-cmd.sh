#!/bin/sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PRIVATE_KEY="/Volumes/SECURITY/Saphir/abuild/saphir.rsa"
if [ -z "$SAPHIR_SOURCE_PATH" ]; then
    SAPHIR_SOURCE_PATH="/Users/tristanisrael/Documents/Sources/Saphir"
fi 
if [ -z "$LOCAL_CACHE" ]; then 
    LOCAL_CACHE="/Users/tristanisrael/Downloads/abuild_cache"
fi
if [ -z "$OUTPUT_REPOSITORY" ]; then 
    OUTPUT_REPOSITORY="Users/tristanisrael/Downloads/abuild_repo"
fi
DOCKER_PATH="/usr/local/bin"
IMAGE_NAME="saphir-dev"
DOCKER_NAME="saphir-dev"
STAGE="dev"
LOCAL_ARCH=$(docker info --format '{{.Architecture}}')
EMULATE=0
MOUNT_REPO=""
INTERACTIVE=""

if [ $LOCAL_ARCH != "amd64" ] && [ $LOCAL_ARCH != "x86_64" ]; then
    echo "Must emulate x86_64 architecture..."
    EMULATE=1
fi

if [ -n "$OVERRIDE_REPOSITORIES" ]; then 
    echo "Override repositories in the container"
    MOUNT_REPO="--mount type=bind,source=$SCRIPT_DIR/repositories,target=/etc/apk/repositories,readonly"
    PIP_REPO="--mount type=bind,source=$SCRIPT_DIR/pip.conf,target=/home/builder/.pip/pip.conf,readonly"
fi

if [ $EMULATE -eq 1 ]; then
    echo "Start emulated Docker"

    if [ "$#" -lt 1 ]; then 
        echo "Starting container with TTY terminal"

        # Run the container
        "$DOCKER_PATH/docker" run \
        -it \
        --rm \
        --platform linux/amd64 \
        $MOUNT_REPO \
        $PIP_REPO \
        --mount type=bind,source=$PRIVATE_KEY,target=/home/builder/.abuild/saphir.rsa,readonly \
        -v "$SAPHIR_SOURCE_PATH:/home/builder/src/saphir" \
        -v "$LOCAL_CACHE:/var/cache/distfiles" \
        -v "$OUTPUT_REPOSITORY:/home/builder/packages/saphir" \
        -e STAGE="$STAGE" \
        --name "$DOCKER_NAME" \
        --network safecor_safecor \
        "$IMAGE_NAME" 
    else 
        echo "Starting docker with a command"

        # Run the container
        "$DOCKER_PATH/docker" run \
        --rm \
        --platform linux/amd64 \
        $MOUNT_REPO \
        $PIP_REPO \
        --mount type=bind,source=$PRIVATE_KEY,target=/home/builder/.abuild/saphir.rsa,readonly \
        -v "$SAFECOR_SOURCE_PATH:/home/builder/src/saphir" \
        -v "$LOCAL_CACHE:/var/cache/distfiles" \
        -v "$OUTPUT_REPOSITORY:/home/builder/packages/saphir" \
        -e STAGE="$STAGE" \
        --name "$DOCKER_NAME" \
        --network safecor_safecor \
        "$IMAGE_NAME" \
        sh -c "$@"
    fi
else
    echo "Start native Docker"

    if [ "$#" -lt 1 ]; then 
        echo "Starting container with TTY terminal"

        # Run the container
        "$DOCKER_PATH/docker" run \
        --rm \
        -it \
        $MOUNT_REPO \
        $PIP_REPO \
        -v "$PRIVATE_KEY:/home/builder/.abuild/saphir.rsa:ro" \
        -v "$SAPHIR_SOURCE_PATH:/home/builder/src/saphir" \
        -v "$LOCAL_CACHE:/var/cache/distfiles" \
        -v "$OUTPUT_REPOSITORY:/home/builder/packages/saphir" \
        -e STAGE="$STAGE" \
        --name "$DOCKER_NAME" \
        --network safecor_safecor \
        "$IMAGE_NAME" 
    else 
        echo "Starting docker with a command"

        # Run the container
        "$DOCKER_PATH/docker" run \
        --rm \
        $MOUNT_REPO \
        $PIP_REPO \
        --mount type=bind,source=$PRIVATE_KEY,target=/home/builder/.abuild/saphir.rsa,readonly \
        -v "$SAPHIR_SOURCE_PATH:/home/builder/src/saphir" \
        -v "$LOCAL_CACHE:/var/cache/distfiles" \
        -v "$OUTPUT_REPOSITORY:/home/builder/packages/safesaphiror" \
        -e STAGE="$STAGE" \
        --name "$DOCKER_NAME" \
        --network safecor_safecor \
        "$IMAGE_NAME" \
        sh -c "$@"
    fi
fi
