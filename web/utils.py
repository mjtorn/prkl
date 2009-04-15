# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.utils.http import int_to_base36

import datetime

def gen_reg_token(true_id, username):
    microsec = datetime.datetime.now().microsecond
    microsec_36 = int_to_base36(microsec)
    true_id = str(true_id)
    raw = '%s-%s%s-%s' % (microsec_36, true_id[:4], true_id[-4:], username)

    return raw

# EOF

