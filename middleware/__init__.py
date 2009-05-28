# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf import settings

from django.http import HttpResponseRedirect

from prkl.web import models

import datetime

import sha

class TrueIdMiddleware(object):
    def gen_true_id(self):
        """Something more random would be nice
        """

        true_id = sha.sha('%s|%s|%s' % (datetime.datetime.now().isoformat(), datetime.datetime.now().microsecond, datetime.datetime.now().microsecond)).hexdigest()

        return true_id

    def process_request(self, request):
        # Did we just fake an entry in cookies?
        request.has_session = (request.session.session_key == request.COOKIES.get('sessionid', ''))
        if not request.COOKIES.has_key('true_id'):
            true_id = self.gen_true_id()
            true_id_ob = models.TrueId.objects.create(hash=true_id)

            # Move this below to process_response
            """
            if not request.has_session:
                request.COOKIES['true_id'] = true_id
            else:
                response = HttpResponseRedirect(request.META['PATH_INFO'])
                response.set_cookie('true_id', true_id_ob.hash, max_age=(2**32)-1, domain=settings.COOKIE_DOMAIN)
                return response
            """
        else:
            true_id = request.COOKIES['true_id']

            try:
                true_id_ob = models.TrueId.objects.get(hash=true_id)
            except models.TrueId.DoesNotExist:
                # Just to be sure we didn't get tampered, recreate the id
                true_id = self.gen_true_id()
                true_id_ob = models.TrueId.objects.create(hash=true_id)

        request.true_id = true_id_ob

#        print 'cookies', request.COOKIES['true_id']
        print 'request.true_id', request.true_id

    def process_response(self, request, response):
        print 'response', id(response)

        ## WTF
        #if not request.has_session:
        #    request.COOKIES['true_id'] = true_id
        #else:
        #if True:
        if not request.COOKIES.has_key('true_id'):
            print 'wtf here'
            #response = HttpResponseRedirect(request.META['PATH_INFO'])
            response.set_cookie('true_id', request.true_id.hash, max_age=(2**32)-1, domain=settings.COOKIE_DOMAIN)
            return response
        return response

# EOF

