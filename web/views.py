# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate, login

from django.http import HttpResponseRedirect

from django.shortcuts import render_to_response

from django.template import RequestContext

from web import forms, models

def dec_login(func):
    def wrap(*args, **kwargs):
        req_ctx = args[1]
        request = req_ctx['request']

        data = request.POST.copy() or None

        login_form = forms.LoginForm(data)

        if not request.user.id:
            if request.POST.get('submit', '') == 'Kirjaudu' and login_form.is_valid():
                username = request.POST.get('username', None)
                password = request.POST.get('password', None)
                if username and password:
                    user = authenticate(username=username, password=password)
                    login(request, user)

                    return HttpResponseRedirect(request.META['PATH_INFO'])
            req_ctx['login_form'] = login_form
        else:
            req_ctx['login_form'] = None

        return func(*args, **kwargs)
    return wrap

render_to_response = dec_login(render_to_response)

# Create your views here.

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

