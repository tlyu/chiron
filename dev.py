#!/usr/bin/python

import sys

import chiron
import main

def init_match_engine():
    match_engine = chiron.MatchEngine()
    main.add_default_fetchers(match_engine)
    main.add_default_matchers(match_engine)
    return match_engine

if __name__ == '__main__':
    print "Configuring standard matchers and fetchers."
    match_engine = init_match_engine()

    subs = sys.argv[1:]
    print "Setting up personals, plus %s" % (subs, )
    if subs:
        match_engine.add_classes(subs)

    print ""
    chiron.main(match_engine)
