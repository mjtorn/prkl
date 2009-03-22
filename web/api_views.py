# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth.models import AnonymousUser

from django.http import HttpResponse

from django.utils import simplejson

from web import forms
from web import models

import datetime

def extend_vip(request, username, period):
    """Extend username's vip by period
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

    period = datetime.timedelta(days=int(period))

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

def post_prkl(request):
    """For posting
    """

    # Default here
    user = AnonymousUser()

    # TODO: Check sms gateway IP here
    # Remember to strip, POST data may contain newlines and stuff
    phone = request.POST.get('phone', '').strip()
    if phone:
        from urllib import unquote
        phone = unquote(phone)
        try:
            user = models.User.objects.get(phone=phone)
        except models.User.DoesNotExist:
            pass

    data = request.POST.copy() or None

    form = forms.SubmitPrklForm(data)

    context = {}

    if form.is_bound:
        if form.is_valid():
            form.data['user'] = user
            form.save()
            context['status'] = 'OK'
            context['message'] = 'Prkl added successfully'
            context['errors'] = []

            ctx = simplejson.dumps(context)

            return HttpResponse(ctx, content_type='text/json')

    context['status'] = 'NOK'
    context['message'] = 'Invalid form data'
    context['errors'] = form.errors

    ctx = simplejson.dumps(context)

    return HttpResponse(ctx, content_type='text/json')

    

# EOF

