# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db import connection

import itertools

###
### Special query object to work around Django suck
###

class PrklQuery(object):
    RAW_QRY = """\
SELECT p.id, p.content, p.content_html, p.score, p.created_at, p.comment_count,
        %(vote_snippet_qry)s,
        %(like_snippet_qry)s
        u.id, u.username,
        wu.vip_expire_at >= NOW() AS is_vip,
        wu.pic,
        t.id, t.name
FROM web_prkl p
    LEFT OUTER JOIN web_user wu ON p.user_id=wu.user_ptr_id
    LEFT OUTER JOIN auth_user u ON wu.user_ptr_id=u.id
    LEFT OUTER JOIN web_prkl_tag pt ON p.id=pt.prkl_id
    LEFT OUTER JOIN web_tag t ON pt.tag_id=t.id
    %(join_like_snippet)s
WHERE p.id IN (
    SELECT web_prkl.id FROM web_prkl
    %(tag)s
    ORDER BY %(order_by)s %(default_extra_order)s
    %(limit)s
)
%(specific_prkl_snippet_qry)s
%(filter_like_user_qry)s
ORDER BY %(order_by)s %(default_extra_order)s
"""

    VOTE_SNIPPET_USERID_QRY = """\
NOT EXISTS(SELECT 1 FROM web_prklvote WHERE prkl_id=p.id AND user_id=%d)
"""

    VOTE_SNIPPET_TRUEID_QRY = """\
NOT EXISTS(SELECT 1 FROM web_prklvote, web_trueid WHERE prkl_id=p.id AND web_prklvote.trueid_id=web_trueid.id AND web_trueid.hash='%s')
"""

    LIKE_SNIPPET_USERID_QRY = """\
EXISTS(SELECT 1 FROM web_prkllike WHERE prkl_id=p.id AND user_id=%d)
"""

    COUNT_PRKL_QRY = """\
SELECT COUNT(web_prkl.id) FROM web_prkl
"""

    TAG_SNIPPET_QRY = """\
, web_prkl_tag, web_tag 
    WHERE web_tag.id=web_prkl_tag.tag_id
    AND web_prkl_tag.prkl_id=web_prkl.id
    AND LOWER(web_tag.name)= LOWER('%s')
"""

    SPECIFIC_PRKL_SNIPPET_QRY = """\
AND p.id= %d
"""

    JOIN_LIKE_SNIPPET = """\
LEFT OUTER JOIN web_prkllike pl ON p.id=pl.prkl_id
"""

    JOIN_LIKED_OF_SNIPPET = """\
LEFT OUTER JOIN web_prkllike pl ON p.id=pl.prkl_id
LEFT OUTER JOIN web_prkl likeprkl ON pl.prkl_id= likeprkl.id
"""

    FILTER_LIKE_USER_QRY = """
AND pl.user_id= %d
"""

    FILTER_LIKED_OF_USER_QRY = """
AND likeprkl.user_id= %d
"""

    def __init__(self, **kwargs):
        # Everything related to the query here
        self.opts = {}
        self.db_res = None
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
            self.opts['like_snippet_qry'] = 'NULL, '

        ## Default order
        self.opts['order_by'] = 'created_at DESC'
        self.opts['default_extra_order'] = ', p.id, u.id, t.id'

        ## No limit by default
        self.opts['limit'] = ''

        ## No specific tag to filter on
        self.opts['tag'] = ''

        ## Filtering on one?
        if kwargs.has_key('prkl_id'):
            self.opts['specific_prkl_snippet_qry'] = self.SPECIFIC_PRKL_SNIPPET_QRY % kwargs['prkl_id']
        else:
            self.opts['specific_prkl_snippet_qry'] = ''

        ## Liked by a user?
        if kwargs.has_key('liked_by'):
            self.opts['join_like_snippet'] = self.JOIN_LIKE_SNIPPET
            self.opts['filter_like_user_qry'] = self.FILTER_LIKE_USER_QRY % kwargs['liked_by']
        else:
            self.opts['join_like_snippet'] = ''
            self.opts['filter_like_user_qry'] = ''

        ## Liked by anyone for a user?
        if kwargs.has_key('liked_of'):
            self.opts['join_like_snippet'] = self.JOIN_LIKED_OF_SNIPPET
            self.opts['filter_like_user_qry'] = self.FILTER_LIKED_OF_USER_QRY % kwargs['liked_of']
        else:
            self.opts['join_like_snippet'] = self.opts['join_like_snippet']
            self.opts['filter_like_user_qry'] = self.opts['filter_like_user_qry']

    def __len__(self):
        if self.res is None:
            cursor = connection.cursor()
            ## Check if we care about a tag
            qry = self.COUNT_PRKL_QRY
            if self.opts['tag']:
                qry = '%s %s ' % (qry, self.opts['tag'])
            cursor.execute(qry)
            # THERE CAN BE ONLY ONE!
            return cursor.fetchone()[0]

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

            return self.get_res()

        return self.res[item]

    def disable_votes(self):
        self.opts['vote_snippet_qry'] = 'false'

    def disable_likes(self):
        self.opts['like_snippet_qry'] = 'false, '

    def top(self):
        self.opts['order_by'] = 'score DESC, created_at DESC'
        self.opts['default_extra_order'] = ', p.id, u.id, t.id'

    def bottom(self):
        self.opts['order_by'] = 'score ASC, created_at DESC'
        self.opts['default_extra_order'] = ', p.id, u.id, t.id'

    def random(self):
        self.opts['order_by'] = 'random()'
        self.opts['default_extra_order'] = ''

    def tag(self, tag_name):
        self.opts['tag'] = self.TAG_SNIPPET_QRY % tag_name

    def execute(self):
        qry = self.RAW_QRY % self.opts 

        cursor = connection.cursor()
        cursor.execute(qry)
        self.db_res = cursor.fetchall()

    def get_res(self):
        if self.db_res is None:
            self.execute()

        IDX_P_ID = 0
        IDX_V_ID = 6
        IDX_L_ID = 7
        IDX_U_ID = 8
        IDX_T_ID = 12
        g = itertools.groupby(self.db_res, lambda x: x[IDX_P_ID])
        prkl_list = []
        prkl_ptr_dict = {}
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
                        prkl_dict['user']['is_vip'] = group[IDX_U_ID + 2]
                        # Hax
                        pic = group[IDX_U_ID + 3]
                        if pic:
                            pic_name, ext = pic.rsplit('.', 1)
                            pic_25 = '%s.25x25.%s' % (pic_name, ext)
                            pic_50 = '%s.50x50.%s' % (pic_name, ext)
                            pic_250 = '%s.250x250.%s' % (pic_name, ext)
                            prkl_dict['user']['pic'] = pic
                            prkl_dict['user']['pic_url_25x25'] = pic_25
                            prkl_dict['user']['pic_url_50x50'] = pic_50
                            prkl_dict['user']['pic_url_250x250'] = pic_25
                        else:
                            prkl_dict['user']['pic'] = ''
                            prkl_dict['user']['pic_url_25x25'] = ''
                            prkl_dict['user']['pic_url_50x50'] = ''
                            prkl_dict['user']['pic_url_250x250'] = ''
                        done_user = True

                    if not done_prkl:
                        prkl_dict['content'] = group[IDX_P_ID + 1]
                        prkl_dict['content_html'] = group[IDX_P_ID + 2]
                        prkl_dict['score'] = group[IDX_P_ID + 3]
                        prkl_dict['created_at'] = group[IDX_P_ID + 4]
                        prkl_dict['comment_count'] = group[IDX_P_ID + 5]
                        prkl_dict['can_vote'] = group[IDX_V_ID]
                        prkl_dict['does_like'] = group[IDX_L_ID]

                    if group[IDX_T_ID]:
                        tag = {
                            'id': group[IDX_T_ID],
                            'name': group[IDX_T_ID + 1],
                        }
                        prkl_dict['tags'].append(tag)

                ## Rows come out in random order, so we have
                ## an accounting dictionary of prkls in case
                ## we need to "return to them"
                if not prkl_ptr_dict.has_key(prkl_id):
                    prkl_list.append(prkl_dict)
                    prkl_ptr_dict[prkl_id] = prkl_list[-1]
                else:
                    # All of these are identical except for tags!
                    prkl_ptr_dict[prkl_id]['tags'].append(tag)

            except StopIteration:
                break

        self.res = prkl_list
        return self.res

# EOF

