#!/bin/sh

export PYTHONIOENCODING=utf8
zwrite -c chiron -i prod -m Starting chiron instance...
~/chiron/main.py --classes
zwrite -c chiron -i prod -m Finished running chiron instance.
