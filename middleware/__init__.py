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
        request.has_session = (request.session.session_key == request.COOKIES.get('sessionid', ''))

        ## Create true_id_ob or pull it out of the database
        if not request.COOKIES.has_key('true_id'):
            true_id = self.gen_true_id()
            true_id_ob = models.TrueId.objects.create(hash=true_id)
        else:
            true_id = request.COOKIES['true_id']

            try:
                true_id_ob = models.TrueId.objects.get(hash=true_id)
            except models.TrueId.DoesNotExist:
                # Just to be sure we didn't get tampered, recreate the id
                true_id = self.gen_true_id()
                true_id_ob = models.TrueId.objects.create(hash=true_id)

        request.true_id = true_id_ob

        # By returning None we are able to re-use the request in views
        return None

    def process_response(self, request, response):

        ## If we didn't have a true id cookie in process_request, set it here
        if not request.COOKIES.has_key('true_id'):
            # If it's something "real"
            content_type = response['Content-type']
            if 'text/' in content_type:
                response.set_cookie('true_id', request.true_id.hash, max_age=(2**32)-1, domain=settings.COOKIE_DOMAIN)

        return response

# EOF

