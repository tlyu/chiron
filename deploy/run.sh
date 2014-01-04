#!/bin/sh

export PYTHONIOENCODING=utf8
k5start -v -f ~/Private/daemon-chiron.keytab daemon/chiron.mit.edu -- ~/chiron/main.py --classes
