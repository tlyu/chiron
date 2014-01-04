#!/bin/sh

export PYTHONIOENCODING=utf8
zwrite -c chiron -i prod -m "Starting chiron instance... (args: \"$@\")"
~/chiron/main.py "$@"
zwrite -c chiron -i prod -m "Finished running chiron instance (args: \"$@\")."
