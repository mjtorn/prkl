# vim: tabstop=4 expandtab autoindent shiwftwidth=4 fileencoding=utf-8

from django.db import connection

###
### Special query object to work around Django suck
###

class PrklQuery(object):
    RAW_QRY = """\
SELECT p.id, p.content, p.score, p.created_at,
        %(vote_snippet_qry)s,
        u.id, u.username,
        t.id, t.name
FROM web_prkl p
    LEFT OUTER JOIN web_user wu ON p.user_id=wu.user_ptr_id
    LEFT OUTER JOIN auth_user u ON wu.user_ptr_id=u.id
    LEFT OUTER JOIN web_prkl_tag pt ON p.id=pt.prkl_id
    LEFT OUTER JOIN web_tag t ON pt.tag_id=t.id
ORDER BY p.id, u.id, t.id
"""

    VOTE_SNIPPET_USERID_QRY = """\
NOT EXISTS(SELECT 1 FROM web_prklvote WHERE prkl_id=p.id AND user_id=%d)
"""

    VOTE_SNIPPET_TRUEID_QRY = """\
NOT EXISTS(SELECT 1 FROM web_prklvote WHERE prkl_id=p.id AND true_id='%s')
"""

    def __init__(self, **kwargs):
        # Everything related to the query here
        self.opts = {}

        ## User id or true id for votes
        if kwargs.has_key('vote_userid'):
            vote_snippet_qry = self.VOTE_SNIPPET_USERID_QRY % kwargs['vote_userid']
        elif kwargs.has_key('vote_trueid'):
            vote_snippet_qry = self.VOTE_SNIPPET_TRUEID_QRY % kwargs['vote_trueid']
        else:
            raise KeyError('vote_userid or vote_trueid needed')

        self.opts['vote_snippet_qry'] = vote_snippet_qry

    def execute(self):
        qry = self.RAW_QRY % self.opts 

        return qry

# EOF

