Chiron
======

Chiron is a zephyrbot that listens for zephyrs containing ticket numbers, looks
up the ticket in an appropriate bugtracker, and responds with the ticket title
and URL. Over time, the definition of "bugtracker" has broadened --- it
includes actual bugtrackers like Debathena's, but also MIT class numbers and
bible verses.

Features
--------

- Supports "tickets" in more than two dozen different "bugtracker" instances --- see `bugtrackers.txt` for a list
- Generic support for projects using
    - Trac
    - Github Issues
    - Bugzilla
- Responds to both classed and personal zephyrs
    - For personal zephyrs, will reply-all to CC'd messages

Running
-------

Chiron requires [Evan Broder's
`python-zephyr`](https://github.com/ebroder/python-zephyr).

Chiron must be run with tickets so that it can sub to incoming zephyrs. You may
find [`k5start`](http://www.eyrie.org/~eagle/software/kstart/) helpful for
keeping current tickets available.

For testing or development purposes, you may want to run `dev.py`, which uses
the standard set of bugtrackers, but listens only to personal zephyrs.

In addition, there is one primary Chiron instance, run by Alex Dehnert, which
uses the configuration in `main.py`. Feel free to crib from `main.py` in
setting up your own Chiron instance. However, please ensure that if you run a
Chiron instance it listens on different classes and/or uses different matchers
than the primary instance, so that users don't receive multiple replies to
their zephyrs.
