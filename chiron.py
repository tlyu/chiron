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


seen_timeout = 5 * 60
default_realm = 'ATHENA.MIT.EDU'
parser = etree.HTMLParser(encoding='UTF-8')

def zbody(zgram):
    body = zgram.fields[1] if len(zgram.fields) > 1 else zgram.fields[0]
    return body.decode('utf8')

def build_matcher(regex, flags=0):
    r = re.compile(regex, flags)
    def match(zgram):
        return r.findall(zbody(zgram))
    return match

def instance_matcher(regex, flags=0):
    r = re.compile(regex, flags)
    def match(zgram):
        if zgram.opcode.lower() == 'auto':
            return []
        return r.findall(zgram.instance)
    return match

def is_personal(zgram):
    return bool(zgram.recipient)


#####################
# Code for Fetchers #
#####################

# Generic fetchers (parametrizable by site)

def fetch_bugzilla(url):
    def bugzilla_fetcher(ticket):
        u = '%s/show_bug.cgi?id=%s' % (url, ticket)
        f = urllib.urlopen(u)
        t = etree.parse(f, parser)
        title = t.xpath('string(//span[@id="short_desc_nonedit_display"])')
        if title:
            return u, title
        else:
            return u, None
    return bugzilla_fetcher

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

def fetch_github(user, repo, ):
    def fetch(ticket):
        u = 'https://api.github.com/repos/%s/%s/issues/%s' % (user, repo, ticket, )
        f = urllib.urlopen(u)
        j = json.load(f)
        try:
            return j['html_url'], j['title']
        except KeyError:
            return u, None
    return fetch

# Project-specific fetchers

fetch_cve_rhbz = fetch_bugzilla("https://bugzilla.redhat.com")
def fetch_cve(ticket):
    # Try fetching from RHBZ first, since it tends to be better
    url, title = fetch_cve_rhbz(ticket)
    print "RHBZ url='%s' title='%s'" % (url, title)
    if title:
        return url, "[RHBZ] " + title

    u = 'http://cve.mitre.org/cgi-bin/cvename.cgi?name=%s' % ticket
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    title = t.xpath('string(//tr[th="Description"]/following::tr[1])')
    if title:
        return u, "\n" + title.strip() + "\n"
    else:
        return u, None

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

def fetch_debbugs(url):
    def debbugs_fetcher(ticket):
        u = '%s/cgi-bin/bugreport.cgi?bug=%s' % (url, ticket)
        f = urllib.urlopen(u)
        t = etree.parse(f, parser)
        title = t.xpath('normalize-space(//h1/child::text()[2])')
        if title:
            return u, title
        else:
            return u, None
    return debbugs_fetcher

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

def fetch_mit_class(ticket):
    u = 'http://student.mit.edu/catalog/search.cgi?search=%s' % (ticket, )
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    title = t.xpath('string(//h3)')
    if title:
        return u, title
    else:
        return u, None

def undebathena_fun():
    u = 'http://debathena.mit.edu/trac/wiki/PackageNamesWeDidntUse'
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    package = choice(t.xpath('id("content")//li')).text.strip()
    dir = choice(['/etc', '/bin', '/usr/bin', '/sbin', '/usr/sbin',
                  '/dev/mapper', '/etc/default', '/var/run'])
    file = choice(os.listdir(dir))
    return u, "%s should divert %s/%s" % (package, dir, file)

def fetch_bible(verse):
    u = 'http://www.esvapi.org/v2/rest/passageQuery?key=IP&passage=%s&output-format=plain-text' % (urllib.quote_plus(verse), )
    bible_text = urllib.urlopen(u).read()
    copyright = "(From The Holy Bible, English Standard Version. See http://www.crosswaybibles.org and http://www.esvapi.org/.)"
    text = "\n%s\n%s" % (bible_text, copyright, )
    return u, text

def fetch_xkcd(comic):
    u = 'http://xkcd.com/%s/' % (comic, )
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    title = t.xpath('string(//title)')
    if title and f.getcode() == 200:
        return u, title
    else:
        return u, None

def fetch_unicode(codepoint):
    u = 'http://www.fileformat.info/info/unicode/char/%s/index.htm' % (codepoint, )
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    title = t.xpath('string(//title)')
    if title and f.getcode() == 200:
        return u, title + ': ' + unichr(int(codepoint, 16))
    else:
        return u, None

def fetch_unicode_char(character):
    codepoint = format(ord(character), 'x')
    u = 'http://www.fileformat.info/info/unicode/char/%s/index.htm' % (codepoint, )
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    title = t.xpath('string(//title)')
    if title and f.getcode() == 200:
        return u, title
    else:
        return u, "U+%s" % (codepoint, )

def fetch_airport(code):
    u = 'http://www.gcmap.com/airport/%s' % (code, )
    f = urllib.urlopen(u)
    t = etree.parse(f, parser)
    place = t.xpath('string(//meta[@name="geo.placename"]/@content)')
    name = t.xpath('string(//td[@class="fn org"])')
    if place and f.getcode() == 200:
        if name:
            title = "%s (%s)" % (place, name, )
        else:
            title = place
        return u, title
    else:
        return u, None


# Special constant-text fetchers

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


#########################################
# Declarations of MATCHERS and FETCHERS #
#########################################

class MatchEngine(object):
    def __init__(self, ):
        self.classes = []
        self.fetchers = {}
        self.matchers = []

    def add_classes(self, classes):
        self.classes.extend(classes)

    def add_fetchers(self, fetchers):
        for name, fetcher in fetchers.items():
            assert name not in self.fetchers
            self.fetchers[name] = fetcher

    def add_matcher(self, fetcher, regexp, cond=False, classes=True, flags=re.I, ):
        assert fetcher in self.fetchers
        if cond:
            pass
        elif classes == True:
            cond = lambda m: True
        else:
            cond = lambda m: (len([cls for cls in classes if cls in m.cls]) > 0)
        self.matchers.append((fetcher, [build_matcher(regexp, flags)], cond))

    def add_trac(self, name, url, classes=None):
        lname = name.lower()
        if classes is None:
            classes = [lname]
        assert name not in self.fetchers
        self.fetchers[name] = fetch_trac(url)
        self.add_matcher(name, r'\b%s[-\s:]*#([0-9]{1,5})\b' % (lname, ))
        self.add_matcher(name, r'\btrac[-\s:]*#([0-9]{1,5})\b', classes=classes)
        # The "-Ubuntu" bit ignores any "uname -a" snippets that might get zephyred
        self.add_matcher(name, r'#([0-9]{2,5})\b(?!-Ubuntu)', classes=classes)

    def find_ticket_info(self, zgram):
        for tracker, ms, cond in self.matchers:
            if cond(zgram):
                for m in ms:
                    ticket = m(zgram)
                    for t in ticket:
                        yield tracker, self.fetchers[tracker], t


#############
# CORE CODE #
#############

def strip_default_realm(principal):
    if '@' in principal:
        user, domain = principal.split('@')
        if domain == default_realm:
            return user
    return principal

def add_default_realm(principal):
    if '@' in principal:
        return principal
    else:
        return "%s@%s" % (principal, default_realm, )

def zephyr_setup(classes):
    zephyr.init()
    subs = zephyr.Subscriptions()
    for c in classes:
        subs.add((c, '*', '*'))
    subs.add(('message', '*', '%me%'))

cc_re = re.compile(r"CC:(?P<recips>( [a-z./@]+)+) *$", re.MULTILINE)

def is_personal(zgram):
    # recipient nonempty -> personal
    return "" != zgram.recipient

def format_tickets(last_seen, zgram, tickets):
    messages = []
    for tracker, fetcher, ticket in tickets:
        print "Found ticket at %s on -c %s: %s, %s" % (datetime.datetime.now(), zgram.cls, tracker, ticket, )
        old_enough = (last_seen.get((tracker, ticket, zgram.cls), 0) < time.time() - seen_timeout)
        if is_personal(zgram): # for personals, don't bother tracking age
            old_enough = True
        if (zgram.opcode.lower() != 'auto' and old_enough):
            if zgram.cls[:2] == 'un':
                u, t = undebathena_fun()
            else:
                u, t = fetcher(ticket)
            if not t:
                t = 'Unable to identify ticket %s' % ticket
            message = '%s ticket %s: %s' % (tracker, ticket, t)
            messages.append((message, u))
            last_seen[(tracker, ticket, zgram.cls)] = time.time()
    return messages

def send_response(zgram, messages):
    z = zephyr.ZNotice()
    z.cls = zgram.cls
    z.instance = zgram.instance
    #z.format = "http://zephyr.1ts.org/wiki/df"
    recipients = set()
    directed = False
    if is_personal(zgram):
        recipients.add(zgram.sender)
        cc = cc_re.match(zbody(zgram))
        if cc:
            cc_recips = cc.group('recips').split(' ')
            for cc_recip in cc_recips:
                if cc_recip and 'chiron' not in cc_recip:
                    recipients.add(add_default_realm(cc_recip.strip()))
        if zgram.opcode == "":
            directed = True
        z.sender = zgram.recipient
    else:
        recipients.add(zgram.recipient)
    z.opcode = 'auto'
    if len(messages) > 1:
        body = '\n'.join(["%s (%s)" % (m, url) for m, url in messages])
    elif len(messages) > 0:
        body = '\n'.join([m for m, url in messages])
    else:
        url = "https://github.com/sipb/chiron"
        body = "No ticket number found in message."
    if len(recipients) > 1:
        cc_line = " ".join([strip_default_realm(r) for r in recipients])
        body = "CC: %s\n%s" % (cc_line, body)
    z.fields = [url, body]
    print '  -> Reply to: %s (original zephyr was to "%s")' % (recipients, zgram.recipient, )
    if messages or directed:
        for recipient in recipients:
            z.recipient = recipient
            z.send()

def main(match_engine):
    last_seen = {}
    zephyr_setup(match_engine.classes)
    print "Listening..."
    while True:
      try:
        zgram = zephyr.receive(True)
        if not zgram:
            continue
        if zgram.opcode.lower() == 'kill':
            sys.exit(0)
        orig_class = False
        if "-test" in zgram.cls:
            orig_class = zgram.cls
            zgram.cls = zgram.instance
        tickets = match_engine.find_ticket_info(zgram)
        messages = format_tickets(last_seen, zgram, tickets)
        if orig_class:
            zgram.cls = orig_class
        send_response(zgram, messages)
      except UnicodeDecodeError:
        pass
