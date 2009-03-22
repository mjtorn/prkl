# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.http import HttpResponse

from django.utils import simplejson

from web import models

import datetime

def extend_vip(request, username):
    """Extend username's vip by 30 days
    """

    context = {
        'status': 'NOK',
        'message': 'Raw structure',
        'errors': [],
    }

    try:
        user = models.User.objects.get(username__iexact=username)
    except models.User.DoesNotExist, msg:
        context['message'] = unicode(msg)
        context['errors'] = (unicode(msg),)

        ctx = simplejson.dumps(context)

        return HttpResponse(ctx, content_type='text/json', status=404)

    period = datetime.timedelta(days=30)

    try:
        user.extend_vip(period)

        context['status'] = 'OK'
        context['message'] = 'VIP extended successfully'
    except AttributeError:
        now = datetime.datetime.now()
        user.set_vip(now + period)

        context['status'] = 'OK'
        context['message'] = 'VIP added successfully'

    ctx = simplejson.dumps(context)

    return HttpResponse(ctx, content_type='text/json')


# EOF

