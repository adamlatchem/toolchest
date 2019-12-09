#!/bin/bash
#
# Convert a blender .blend file to json format.
# Useful as a textconv in a VCS.
#
if [ $# -ne 1 ]; then
    echo "usage: ${BASH_SOURCE} blend-file-name"
    exit 1
fi

BLENDER=/Applications/Blender.app/Contents/MacOS/Blender
BLENDFILE=$1
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
TMPFILE="$(mktemp)"

"$BLENDER" \
    --log-file /dev/null \
    -b "$BLENDFILE" \
    -P "$DIR/blend2json.py" \
    -- "$TMPFILE" \
    >/dev/null

cat "$TMPFILE"
rm "$TMPFILE"
