# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate, login

from django.http import HttpResponseRedirect

from django.shortcuts import render_to_response

from django.template import RequestContext

from web import forms, models

def dec_login(func):
    def wrap(*args, **kwargs):
        request = args[0]

        if request.POST and not request.user.id:
            username = request.POST.get('username', None)
            password = request.POST.get('password', None)
            if username and password:
                user = authenticate(username=username, password=password)
                if user:
                    login(request, user)

                return HttpResponseRedirect(request.META['PATH_INFO'])
        return func(*args, **kwargs)
    return wrap

# Create your views here.

@dec_login
def index(request):
    """Our index page
    """

    data = request.POST.copy() or None
    if data:
        data['user'] = request.user

    submit_prkl_form = forms.SubmitPrklForm(data)

    if submit_prkl_form.is_bound:
        if submit_prkl_form.is_valid():
            submit_prkl_form.save()
            
            return HttpResponseRedirect(request.META['PATH_INFO'])

    prkls = models.Prkl.objects.all().order_by('-created_at')

    context = {
        'title': 'Etusivu',
        'form': submit_prkl_form,
        'prkls': prkls,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)


@dec_login
def top(request):
    """The best
    """

    prkls = models.Prkl.objects.all()
    if request.user.id:
        prkls = prkls.extra({'can_vote': 'SELECT true'})
    else:
        prkls = prkls.extra({'can_vote': 'SELECT false'})
    prkls = prkls.order_by('-score', 'created_at')

    context = {
        'title': 'Parhaat',
        'prkls': prkls,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)

@dec_login
def bottom(request):
    """The worst
    """

    prkls = models.Prkl.objects.all()
    if request.user.id:
        prkls = prkls.extra({'can_vote': 'SELECT false'})
    else:
        prkls = prkls.extra({'can_vote': 'SELECT true'})
    prkls = prkls.order_by('score', '-created_at')

    context = {
        'title': 'Huonoimmat',
        'prkls': prkls,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)

# EOF

