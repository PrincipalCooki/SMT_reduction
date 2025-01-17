#!/usr/bin/env bash

SCRIPTPATH="$( cd -- "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

FSYNTH=${FSYNTH:-"$SCRIPTPATH/fsynth.py"}
N2X=${N2X:-"$SCRIPTPATH/network2x.py"}

IMAGE=$(basename $1).png

cat $1 | ${FSYNTH} | $N2X --to-dot - | dot -Tpng -o $IMAGE && xdg-open $IMAGE

