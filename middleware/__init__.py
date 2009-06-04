# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.csrf import middleware as csrf_middleware
from django.contrib.sessions import middleware as sessions_middleware

from django.conf import settings

from django.http import HttpResponseForbidden

from prkl.web import models

import datetime

import sha

class SessionMiddleware(sessions_middleware.SessionMiddleware):
    """Accept '' as session key
    """

    def process_request(self, request):
        retval = super(SessionMiddleware, self).process_request(request)

        if not request.COOKIES.has_key(settings.SESSION_COOKIE_NAME):
            request.COOKIES[settings.SESSION_COOKIE_NAME] = ''
        elif request.COOKIES[settings.SESSION_COOKIE_NAME] is None:
            request.COOKIES[settings.SESSION_COOKIE_NAME] = ''

        return retval


class CsrfMiddleware(csrf_middleware.CsrfMiddleware):
    """Hack csrf to work with empty session
    THIS MAKES THE SITE VULNERABLE - EVERY COOKIELESS "SESSION" HAS THE SAME
    CSRF KEY, BASED ON THE DJANGO INSTALLATION'S SECRET_KEY!!!
    """

    def process_request(self, request):
        if request.method == 'POST' and request.POST.get('csrfmiddlewaretoken', None):
            retval = super(CsrfMiddleware, self).process_request(request)

            ## Forbidden can come from not having the key in POST and also
            ## from a bad value.
            if isinstance(retval, HttpResponseForbidden):
                # See if we compare to the horrible default value
                insecure_crap_token = csrf_middleware._make_token('')
                if request.POST['csrfmiddlewaretoken'] == insecure_crap_token:
                    return None

            return retval


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
                cookie_domain = request.META['HTTP_HOST'].split(':')[0]
                response.set_cookie('true_id', request.true_id.hash, max_age=(2**32)-1, domain=cookie_domain)

        return response

# EOF

