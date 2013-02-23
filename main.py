#!/usr/bin/python
import debothena

match_engine = debothena.MatchEngine()

match_engine.add_classes([
        'broder-test', 'geofft-test', 'adehnert-test',
        'linerva', 'debathena', 'undebathena', 'consult',
        'sipb', 'sipb-auto', 'scripts', 'barnowl', 'zephyr-dev', 'xvm',
        'geofft', 'lizdenys', 'jdreed', 'axs', 'adehnert', 'achernya', 'kcr', 'jesus', 'nelhage',
        'assassin',
        'remit', 'asa', 'esp',
    ])

match_engine.add_fetchers({
    'CVE': debothena.fetch_cve,
    'Launchpad': debothena.fetch_launchpad,
    'Debian': debothena.fetch_debbugs('http://bugs.debian.org'),
    'Debothena': debothena.fetch_github('sipb', 'debothena'),
    'zcommit': debothena.fetch_github('sipb', 'zcommit'),
    'RHBZ': debothena.fetch_bugzilla('https://bugzilla.redhat.com'),
    'pag-screen': debothena.fetch_github('sipb', 'pag-screen'),
    'Mosh': debothena.fetch_github('keithw', 'mosh'),
    'Scripts FAQ': debothena.fetch_scripts_faq,
    'ESP': debothena.fetch_github('learning-unlimited', 'ESP-Website'),
    'Pokedex': debothena.fetch_pokemon,
    'MIT Class': debothena.fetch_mit_class,
    'Bible': debothena.fetch_bible,
    'XKCD': debothena.fetch_xkcd,
    'Unicode': debothena.fetch_unicode,
    'Assassin': debothena.deal_with_assassin,
    'SCIENCE': debothena.invoke_science,
    'Debothena Test': debothena.invoke_debothena,
    })

match_engine.add_matcher('CVE',         r'\b(CVE-[0-9]{4}-[0-9]{4})\b')
match_engine.add_matcher('Launchpad',   r'\blp[-\s:]*#([0-9]{4,8})\b')
match_engine.add_matcher('Debian',      r'\bdebian[-\s:]#([0-9]{4,6})\b')
match_engine.add_matcher('Debothena',   r'\bdebothena[-\s:]*#([0-9]{1,5})\b')
match_engine.add_matcher('zcommit',     r'\bzcommit[-\s:]*#([0-9]{1,5})\b')
match_engine.add_matcher('RHBZ',        r'\bRHBZ[-\s:]#([0-9]{4,7})\b')
match_engine.add_matcher('pag-screen',  r'\bpag-screen[-\s:]*#([0-9]{1,5})\b')
match_engine.add_matcher('Mosh',        r'\bmosh[-\s:]*#([0-9]{1,5})\b')
match_engine.add_matcher('Scripts FAQ', r'\bscripts faq[-\s:]*#([0-9]{1,5})\b')
match_engine.add_matcher('Scripts FAQ', r'\bfaq[-\s:]*#([0-9]{1,5})\b', classes=['scripts'])
match_engine.add_matcher('ESP',         r'#([0-9]{2,5})\b(?!-Ubuntu)', classes=['esp'])
match_engine.add_matcher('ESP',         r'\besp[-\s:]*#([0-9]{1,5})\b')
match_engine.add_matcher('Pokedex',     r'\bpokemon[-\s:]*#([0-9]{1,3})\b')
match_engine.add_matcher('Pokedex',     r'#([0-9]{1,3})\b', classes=['lizdenys'])
match_engine.add_matcher('MIT Class',   r'class ([0-9a-z]{1,3}[.][0-9a-z]{1,4})\b')
match_engine.add_matcher('MIT Class',   r"what's ([0-9a-z]{1,3}[.][0-9a-z]{1,4})\?\b")
match_engine.add_matcher('MIT Class',   r'([0-9a-z]{1,3}[.][0-9]{1,4})\b', cond=debothena.is_personal)
match_engine.add_matcher('Bible',       r'Bible\(([\w :-]+)\)')
match_engine.add_matcher('XKCD',        r'\bxkcd[-\s:]#([0-9]{1,5})\b')
match_engine.add_matcher('Unicode',     r'\bu\+([0-9a-fA-F]{2,6})\b')
match_engine.add_matcher('Assassin',    r'\bcombo\b', classes=['assassin'])
match_engine.add_matcher('Assassin',    r'\bcombination\b', classes=['assassin'])
match_engine.add_matcher('SCIENCE',     r'^science$', classes=['axs'])
match_engine.add_matcher('Debothena Test', r'\bdebothena test[-\s:]*#([0-9]{1,5})\b')

match_engine.add_trac('Django', 'https://code.djangoproject.com', classes=[])
match_engine.add_trac('Debathena', 'http://debathena.mit.edu/trac', classes=['debathena', 'linerva', 'jdreed', ])
match_engine.add_trac('Scripts', 'http://scripts.mit.edu/trac', )
match_engine.add_trac('XVM', 'http://xvm.scripts.mit.edu/trac', )
match_engine.add_trac('Barnowl', 'http://barnowl.mit.edu', )
match_engine.add_trac('Zephyr', 'http://zephyr.1ts.org', classes=['zephyr-dev'])
match_engine.add_trac('SIPB', 'http://sipb.mit.edu/trac', )
match_engine.add_trac('Remit', 'http://remit.scripts.mit.edu/trac', )
match_engine.add_trac('ASA', 'http://asa.mit.edu/trac', )

if __name__ == '__main__':
    debothena.main(match_engine)
