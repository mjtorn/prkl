# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.utils.http import int_to_base36

from django.conf import settings

import datetime

def gen_reg_token(true_id, username):
    microsec = datetime.datetime.now().microsecond
    microsec_36 = int_to_base36(microsec)
    true_id = str(true_id)
    raw = '%s-%s%s-%s' % (microsec_36, true_id[:4], true_id[-4:], username)

    return raw

def make_tweet(prkl):
    twit_length = 140

    # Forge twitter tag as url in dev
    if settings.PRODUCTION:
        # FIXME: Not dynamic enough
        base_url = 'http://prkl.es/prkl/%d'
        url = base_url % prkl.id
    else:
        url = '#prkldev'

    kw = '#prkl'

    trail = ' %s %s' % (kw, url)
    remains = twit_length - len(trail)

    content_length = len(prkl.content)

    if content_length > remains:
        head = prkl.content[:remains - 3]
        head = '%s...' % head
    else:
        head = prkl.content

    return '%s%s' % (head, trail)

# EOF

