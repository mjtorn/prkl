# vim: tabstop=4 expandtab autoindent shiwftwidth=4 fileencoding=utf-8

from django.db import connection

import itertools

###
### Special query object to work around Django suck
###

class PrklQuery(object):
    RAW_QRY = """\
SELECT p.id, p.content, p.score, p.created_at,
        %(vote_snippet_qry)s,
        %(like_snippet_qry)s
        u.id, u.username,
        t.id, t.name
FROM web_prkl p
    LEFT OUTER JOIN web_user wu ON p.user_id=wu.user_ptr_id
    LEFT OUTER JOIN auth_user u ON wu.user_ptr_id=u.id
    LEFT OUTER JOIN web_prkl_tag pt ON p.id=pt.prkl_id
    LEFT OUTER JOIN web_tag t ON pt.tag_id=t.id
ORDER BY %(order_by)s, p.id, u.id, t.id
%(limit)s
"""

    VOTE_SNIPPET_USERID_QRY = """\
NOT EXISTS(SELECT 1 FROM web_prklvote WHERE prkl_id=p.id AND user_id=%d)
"""

    VOTE_SNIPPET_TRUEID_QRY = """\
NOT EXISTS(SELECT 1 FROM web_prklvote WHERE prkl_id=p.id AND true_id='%s')
"""

    LIKE_SNIPPET_USERID_QRY = """\
EXISTS(SELECT 1 FROM web_prkllike WHERE prkl_id=p.id AND user_id=%d)
"""

    def __init__(self, **kwargs):
        # Everything related to the query here
        self.opts = {}
        self.res = None

        ## User id or true id for votes
        if kwargs.has_key('vote_userid'):
            vote_snippet_qry = self.VOTE_SNIPPET_USERID_QRY % kwargs['vote_userid']
        elif kwargs.has_key('vote_trueid'):
            vote_snippet_qry = self.VOTE_SNIPPET_TRUEID_QRY % kwargs['vote_trueid']
        else:
            raise KeyError('vote_userid or vote_trueid needed')

        self.opts['vote_snippet_qry'] = vote_snippet_qry

        ## Does the user like this?
        if kwargs.has_key('like_userid'):
            like_userid = self.LIKE_SNIPPET_USERID_QRY % kwargs['like_userid']
            # We always have vote_snippet_qry so we always need comma here
            self.opts['like_snippet_qry'] = '%s, ' % like_userid
        else:
            self.opts['like_snippet_qry'] = ''

        ## Default order
        self.opts['order_by'] = 'created_at DESC'

        ## No limit by default
        self.opts['limit'] = ''

    def __len__(self):
        if self.res is None:
            return 0

        return len(self.res)

    def __getitem__(self, item):
        """Re-hit db every time we get a slice
        """
        if isinstance(item, slice):
            # Hngh...
            start, stop, step = item.indices(2**32)

            if start < 0:
                raise ValueError('Negative start not ok')

            if stop < 0:
                raise ValueError('Negative stop not ok')

            limit = stop - start

            if limit < 0:
                raise ValueError('Negative limit not ok')

            if limit:
                self.opts['limit'] = 'LIMIT %d' % limit

                if start:
                    self.opts['limit'] = '%s OFFSET %d' % (self.opts['limit'], start)

            self.execute()

            return self.res

        return self.res[item]

    def disable_votes(self):
        self.opts['vote_snippet_qry'] = 'false'

    def top(self):
        self.opts['order_by'] = 'score DESC, created_at DESC'

    def bottom(self):
        self.opts['order_by'] = 'score ASC, created_at DESC'

    def execute(self):
        qry = self.RAW_QRY % self.opts 

        cursor = connection.cursor()
        cursor.execute(qry)
        self.res = cursor.fetchall()

    def get_res(self):
        if self.res is None:
            self.execute()

        IDX_P_ID = 0
        IDX_V_ID = 4
        IDX_L_ID = 5
        IDX_U_ID = 6
        IDX_T_ID = 8
        g = itertools.groupby(self.res, lambda x: x[IDX_P_ID])
        prkl_list = []
        while True:
            try:
                prkl_dict = {}
                prkl_id, groups = g.next()
                prkl_dict['id'] = prkl_id

                # Simple user
                prkl_dict['user'] = {}

                # Tag list
                prkl_dict['tags'] = []

                done_user = False
                done_prkl = False

                groups = list(groups)
                for group in groups:
                    # The user is always the same for a prkl, foreign key
                    if not done_user and group[IDX_U_ID]:
                        # Simple for user
                        prkl_dict['user']['id']= group[IDX_U_ID]
                        prkl_dict['user']['username'] = group[IDX_U_ID + 1]
                        done_user = True

                    if not done_prkl:
                        prkl_dict['content'] = group[IDX_P_ID + 1]
                        prkl_dict['score'] = group[IDX_P_ID + 2]
                        prkl_dict['created_at'] = group[IDX_P_ID + 3]
                        prkl_dict['can_vote'] = group[IDX_V_ID]
                        prkl_dict['does_like'] = group[IDX_L_ID]

                    if group[IDX_T_ID]:
                        tag = {
                            'id': group[IDX_T_ID],
                            'name': group[IDX_T_ID + 1],
                        }
                        prkl_dict['tags'].append(tag)

                prkl_list.append(prkl_dict)
            except StopIteration:
                break

        return prkl_list

# EOF

