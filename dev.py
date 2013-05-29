#!/usr/bin/python

import debothena
import main

def init_match_engine():
    match_engine = debothena.MatchEngine()
    main.add_default_fetchers(match_engine)
    main.add_default_matchers(match_engine)
    return match_engine

if __name__ == '__main__':
    print "Configuring standard matchers and fetchers, but listening only to personals."
    print ""
    match_engine = init_match_engine()
    debothena.main(match_engine)
