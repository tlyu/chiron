#!/usr/bin/python

import chiron
import main

def init_match_engine():
    match_engine = chiron.MatchEngine()
    main.add_default_fetchers(match_engine)
    main.add_default_matchers(match_engine)
    return match_engine

if __name__ == '__main__':
    print "Configuring standard matchers and fetchers, but listening only to personals."
    print ""
    match_engine = init_match_engine()
    chiron.main(match_engine)
