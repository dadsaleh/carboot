#!/bin/sh
cd "$(dirname "$0")" || exit 1
export MICROPYPATH="src:src/lib:.frozen:$HOME/.micropython/lib:/usr/lib/micropython"

status=0
for t in test/test_*.py; do
    micropython "$t" || status=1
done
exit $status
