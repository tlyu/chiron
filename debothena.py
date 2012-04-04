#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import urllib
from lxml import etree
import time
import datetime
import sys
from random import choice
import os
import json

try:
    import zephyr
except ImportError:
    import site
    site.addsitedir('/mit/broder/lib/python%s/site-packages' % sys.version[:3])
    import zephyr


last_seen = {}
seen_timeout = 5 * 60
parser = etree.HTMLParser(encoding='UTF-8')

def build_matcher(regex, flags=0):
    r = re.compile(regex, flags)
    def match(zgram):
        return r.findall(zgram.fields[1] if len(zgram.fields) > 1 else zgram.fields[0])
    return match

def instance_matcher(regex, flags=0):
    r = re.compile(regex, flags)
    def match(zgram):
        if zgram.opcode.lower() == 'auto':
            return []
        return r.findall(zgram.instance)
    return match

matchers = (
    ('Debathena', [build_matcher(r'\btrac[-\s:]*#([0-9]{2,5})\b', re.I)], lambda m: 'debathena' in m.cls or 'linerva' in m.cls),
    ('Debathena', [build_matcher(r'#([0-9]{2,5})\b(?!-Ubuntu)')], lambda m: 'debathena' in m.cls or 'linerva' in m.cls),
    ('Debathena', [build_matcher(r'\bdebathena[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('Scripts', [build_matcher(r'\btrac[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: 'scripts' in m.cls),
    ('Scripts', [build_matcher(r'#([0-9]{2,5})\b(?!-Ubuntu)')], lambda m: 'scripts' in m.cls),
    ('Scripts', [build_matcher(r'\bscripts[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('Barnowl', [build_matcher(r'\btrac[-\s:]*#([0-9]{2,5})\b', re.I)], lambda m: 'barnowl' in m.cls),
    ('Barnowl', [build_matcher(r'#([0-9]{2,5})\b(?!-Ubuntu)', re.I)], lambda m: 'barnowl' in m.cls),
    ('Barnowl', [build_matcher(r'\bbarnowl[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('ASA', [build_matcher(r'\btrac[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: 'asa' in m.cls),
    ('ASA', [build_matcher(r'#([0-9]{2,5})\b(?!-Ubuntu)', re.I)], lambda m: 'asa' in m.cls),
    ('ASA', [build_matcher(r'\basa[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('ESP', [build_matcher(r'#([0-9]{2,5})\b(?!-Ubuntu)', re.I)], lambda m: 'esp' in m.cls),
    ('ESP', [build_matcher(r'\besp[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('SIPB', [build_matcher(r'\bsipb[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('Scripts FAQ', [build_matcher(r'\bscripts faq[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('Scripts FAQ', [build_matcher(r'\bfaq[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: 'scripts' in m.cls),
    ('Launchpad', [build_matcher(r'\blp[-\s:]*#([0-9]{4,6})\b', re.I)], lambda m: True),
    ('Pokedex', [build_matcher(r'\bpokemon[-\s:]*#([0-9]{1,3})\b', re.I)], lambda m: True),
    ('Pokedex', [build_matcher(r'#([0-9]{1,3})\b', re.I)], lambda m: 'lizdenys' in m.cls or 'zhangc' in m.cls),
    ('Assassin', [build_matcher(r'\bcombo\b', re.I)], lambda m: 'assassin' in m.cls),
    ('Assassin', [build_matcher(r'\bcombination\b', re.I)], lambda m: 'assassin' in m.cls),
    ('SCIENCE', [build_matcher(r'^science$', re.I)], lambda m: 'axs' in m.cls),
    ('Debothena', [build_matcher(r'\bdebothena[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    )

def fetch_trac(url):
    def trac_fetcher(ticket):
        u = '%s/ticket/%s' % (url, ticket)
        f = urllib.urlopen(u)
        t = etree.parse(f, parser)
        title = t.xpath('string(//h2[@class])')
        if title:
            return u, title
        else:
            return u, None
    return trac_fetcher

def fetch_scripts_faq(ticket):
    u = 'http://scripts.mit.edu/faq/%s' % ticket
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    title = t.xpath('string(//h3[@class="storytitle"])')
    if title:
        return u, title
    else:
        return u, None

def fetch_launchpad(ticket):
    u = 'http://api.launchpad.net/1.0/bugs/%s' % ticket
    f = urllib.urlopen(u)
    j = json.load(f)
    try:
        return j['web_link'], j['title']
    except KeyError:
        return u, None

def fetch_github(user, repo, ):
    def fetch(ticket):
        u = 'http://github.com/api/v2/json/issues/show/%s/%s/%s' % (user, repo, ticket, )
        f = urllib.urlopen(u)
        j = json.load(f)
        try:
            issue = j['issue']
            return issue['html_url'], issue['title']
        except KeyError:
            return u, None
    return fetch

def fetch_pokemon(ticket):
    u = 'http://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number'
    f = urllib.urlopen(u + '?action=raw')
    for line in f:
        if line[0:7] == '{{rdex|':
            (id, name) = line.split('|')[2:4]
            try:
                if int(id) == int(ticket):
                    return u, "%s (%s)" % (name, ", ".join(line.split('}')[0].split('|')[5:]))
            except ValueError:
                pass
    return u, None

def deal_with_assassin(ticket):
    return ("NO COMBOS OVER ZEPHYR",
"""DO @b(NOT) ASK FOR OR SEND THE OFFICE COMBO
OVER ZEPHYR, EVEN PERSONAL ZEPHYR.
Instead, look in /mit/assassin/Office. If you don't have access,
ask to be added.""")

def invoke_science(ticket):
    return ("SCIENCE!",
"""
  ____   ____ ___ _____ _   _  ____ _____
 / ___| / ___|_ _| ____| \ | |/ ___| ____|
 \___ \| |    | ||  _| |  \| | |   |  _|
  ___) | |___ | || |___| |\  | |___| |___
 |____/ \____|___|_____|_| \_|\____|_____|
""")

def invoke_debothena(ticket):
    return (ticket,
u"""
╺┳┓┏━╸┏┓ ┏━┓╺┳╸╻ ╻┏━╸┏┓╻┏━┓
 ┃┃┣╸ ┣┻┓┃ ┃ ┃ ┣━┫┣╸ ┃┗┫┣━┫
╺┻┛┗━╸┗━┛┗━┛ ╹ ╹ ╹┗━╸╹ ╹╹ ╹
""")

fetchers = {
    'Debathena': fetch_trac('http://debathena.mit.edu/trac'),
    'Scripts': fetch_trac('http://scripts.mit.edu/trac'),
    'Barnowl': fetch_trac('http://barnowl.mit.edu'),
    'ASA': fetch_trac('http://asa.mit.edu/trac'),
    'SIPB': fetch_trac('http://sipb.mit.edu/trac'),
    'Scripts FAQ': fetch_scripts_faq,
    'Launchpad': fetch_launchpad,
    'Pokedex': fetch_pokemon,
    'Assassin': deal_with_assassin,
    'SCIENCE': invoke_science,
    'Debothena': invoke_debothena,
    'ESP': fetch_github('learning-unlimited', 'ESP-Website'),
    }

def find_ticket_info(zgram):
    for tracker, ms, cond in matchers:
        if cond(zgram):
            for m in ms:
                ticket = m(zgram)
                for t in ticket:
                    yield tracker, t

def undebathena_fun():
    u = 'http://debathena.mit.edu/trac/wiki/PackageNamesWeDidntUse'
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    package = choice(t.xpath('id("content")//li')).text.strip()
    dir = choice(['/etc', '/bin', '/usr/bin', '/sbin', '/usr/sbin',
                  '/dev/mapper', '/etc/default', '/var/run'])
    file = choice(os.listdir(dir))
    return u, "%s should divert %s/%s" % (package, dir, file)

def main():
    zephyr.init()
    subs = zephyr.Subscriptions()
    for c in [
        'broder-test', 'geofft-test', 'adehnert-test',
        'linerva', 'debathena', 'undebathena',
        'sipb', 'scripts', 'barnowl',
        'geofft', 'lizdenys', 'zhangc', 'jdreed', 'axs',
        'assassin',
        'asa', 'esp',
    ]:
        subs.add((c, '*', '*'))
    subs.add(('message', '*', '%me%'))

    while True:
      try:
        zgram = zephyr.receive(True)
        if not zgram:
            continue
        if zgram.opcode.lower() == 'kill':
            sys.exit(0)
        messages = []
        tickets = find_ticket_info(zgram)
        for tracker, ticket in tickets:
            print "Found ticket at %s: %s, %s" % (datetime.datetime.now(), tracker, ticket, )
            fetcher = fetchers.get(tracker)
            if fetcher:
                if (zgram.opcode.lower() != 'auto' and
                    last_seen.get((tracker, ticket, zgram.cls), 0) < time.time() - seen_timeout):
                    if zgram.cls[:2] == 'un':
                        u, t = undebathena_fun()
                    else:
                        u, t = fetcher(ticket)
                    if not t:
                        t = 'Unable to identify ticket %s' % ticket
                    message = '%s ticket %s: %s' % (tracker, ticket, t)
                    messages.append((message, u))
                    last_seen[(tracker, ticket, zgram.cls)] = time.time()
        send_url = (len(messages) > 1)
        if messages:
            z = zephyr.ZNotice()
            z.cls = zgram.cls
            z.instance = zgram.instance
            if 'debothena' in zgram.recipient:
                z.recipient = zgram.sender
                z.sender = zgram.recipient
            else:
                z.recipient = zgram.recipient
                z.sender = 'debothena'
            z.opcode = 'auto'
            if send_url:
                body = '\n'.join(["%s (%s)" % pair for pair in messages])
            else:
                body = '\n'.join([m for m, url in messages])
            z.fields = [u, body]
            z.send()
      except UnicodeDecodeError:
        pass


if __name__ == '__main__':
    main()
