#!/bin/sh

strace -ff -s 4096 -yy -e trace=openat,open,access,readlink,fork,execve -o trace.log lxc-start saphir-container-eset
