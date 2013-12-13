import re

import chiron

try:
    import zephyr
except ImportError:
    import site
    site.addsitedir('/mit/broder/lib/python%s/site-packages' % sys.version[:3])
    import zephyr

default_realm = 'ATHENA.MIT.EDU'

# Used for handling CC's
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

class ZephyrMessage(chiron.Message):
    def __init__(self, zgram):
        self._zgram = zgram

    def body(self):
        fields = self._zgram.fields
        body = fields[1] if len(fields) > 1 else fields[0]
        if type(body) != unicode:
            body = body.decode('utf8')
        return body

    def cls(self): return self._zgram.cls

    def instance(self): return self._zgram.instance

    def sender(self): return self._zgram.sender

    def recipient(self): return self._zgram.recipient

    def is_personal(self):
        return bool(self._zgram.recipient)

    def send_reply(self, messages):
        zgram = self._zgram
        z = zephyr.ZNotice()
        z.cls = zgram.cls
        z.instance = zgram.instance
        #z.format = "http://zephyr.1ts.org/wiki/df"
        # The following default format will cause messages not to be mirrored to MIT Zulip.
        #z.format = "Zephyr error: See http://zephyr.1ts.org/wiki/df"
        recipients = set()
        if self.is_personal():
            recipients.add(zgram.sender)
            cc = cc_re.match(self.body())
            if cc:
                cc_recips = cc.group('recips').split(' ')
                for cc_recip in cc_recips:
                    if cc_recip and 'chiron' not in cc_recip:
                        recipients.add(add_default_realm(str(cc_recip.strip())))
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
        print '  -> Reply to: %s (original message was to "%s")' % (recipients, zgram.recipient, )
        if messages or self.is_personal():
            for recipient in recipients:
                z.recipient = recipient
                z.send()

def main(match_engine):
    zephyr_setup(match_engine.classes)
    print "Listening..."
    while True:
        zgram = zephyr.receive(True)
        if not zgram:
            continue
        if zgram.opcode.lower() == 'kill':
            print "Killing per request -- message:"
            msg.log_arrival()
            sys.exit(0)
        if zgram.opcode.lower() in ('auto', 'ping'):
            continue
        msg = ZephyrMessage(zgram)
        match_engine.process(msg)
