#!/bin/sh
# strace_files_used_clean.sh
# Usage: ./strace_files_used_clean.sh trace.log*

for f in "$@"; do
    grep -E 'openat|open|access|readlink|fork|execve' "$f" |
    # remove some entries
    grep -v 'ENOENT' |
    grep -v 'EINVAL' |
    grep -v '/sys' |
    grep -v '/dev' |
    grep -v '/proc' |
    grep -v '/run' |
    grep -v '/tmp' |
    grep -v '/mnt'
    # extraire tous les chemins commençant par /
    #grep -o '/[^", )]*'
done | sort -u 