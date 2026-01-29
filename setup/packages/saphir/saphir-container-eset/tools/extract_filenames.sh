#!/bin/sh

awk -F'[<>"]' '
{
  for (i = 2; i <= NF; i += 2)
    if ($i ~ /^\//)
      print $i
}
' $1