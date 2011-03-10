#!/usr/bin/python
import re
import urllib
from lxml import etree
import time
import sys
from random import choice
import os

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

matchers = (
    ('Debathena', [build_matcher(r'\btrac[-\s:]*#([0-9]{2,5})\b', re.I)], lambda m: 'debathena' in m.cls),
    ('Debathena', [build_matcher(r'#([0-9]{2,5})\b(?!-Ubuntu)')], lambda m: 'debathena' in m.cls),
    ('Debathena', [build_matcher(r'\bdebathena[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('Scripts', [build_matcher(r'\btrac[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: 'scripts' in m.cls),
    ('Scripts', [build_matcher(r'#([0-9]{1,5})\b(?!-Ubuntu)')], lambda m: 'scripts' in m.cls),
    ('Scripts', [build_matcher(r'\bscripts[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('Scripts FAQ', [build_matcher(r'\bscripts faq[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: True),
    ('Scripts FAQ', [build_matcher(r'\bfaq[-\s:]*#([0-9]{1,5})\b', re.I)], lambda m: 'scripts' in m.cls),
    ('Pokedex', [build_matcher(r'\bpokemon[-\s:]*#([0-9]{1,3})\b', re.I)], lambda m: True),
    ('Pokedex', [build_matcher(r'#([0-9]{1,3})\b', re.I)], lambda m: 'lizdenys' in m.cls or 'zhangc' in m.cls),
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

fetchers = {
    'Debathena': fetch_trac('http://debathena.mit.edu/trac'),
    'Scripts': fetch_trac('http://scripts.mit.edu/trac'),
    'Scripts FAQ': fetch_scripts_faq,
    'Pokedex': fetch_pokemon,
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
    for c in ['broder-test', 'debathena', 'sipb', 'scripts', 'undebathena',
              'geofft', 'geofft-test', 'lizdenys', 'zhangc', 'jdreed']:
        subs.add((c, '*', '*'))

    while True:
      try:
        zgram = zephyr.receive(True)
        if not zgram:
            continue
        if zgram.opcode.lower() == 'kill':
            sys.exit(0)
        messages = []
        for tracker, ticket in find_ticket_info(zgram):
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
                    messages.append('%s ticket %s: %s' % (tracker, ticket, t))
                    last_seen[(tracker, ticket, zgram.cls)] = time.time()
        if messages:
            z = zephyr.ZNotice()
            z.cls = zgram.cls
            z.instance = zgram.instance
            z.recipient = zgram.recipient
            z.opcode = 'auto'
            z.sender = 'debothena'
            z.fields = [u, '\n'.join(messages)]
            z.send()
      except UnicodeDecodeError:
        pass


if __name__ == '__main__':
    main()
