#!/bin/sh

export PYTHONIOENCODING=utf8
while true; do
    zwrite -c chiron -i prod -m "Starting chiron instance... (args: \"$@\")"
    ~/chiron/main.py "$@"
    zwrite -c chiron -i prod -m "Finished running chiron instance (args: \"$@\")."
done
