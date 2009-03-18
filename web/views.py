# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import models as auth_models

from django.core.urlresolvers import reverse

from django.conf import settings

from django.core import mail

from django.http import HttpResponseRedirect

from django.shortcuts import render_to_response

from django.template import RequestContext

from django import template

from web import forms, models

import datetime

import sha

FORGOT_PASSWORD_SUBJECT = 'prkl.es: salasanan vaihto'

def dec_login(func):
    def wrap(*args, **kwargs):
        req_ctx = args[1]
        request = req_ctx['request']

        data = request.POST.copy() or None

        if not request.user.id and data:
            if request.POST.get('submit', '') == 'Kirjaudu':
                login_form = forms.LoginForm(data)
                if login_form.is_valid():
                    username = request.POST.get('username', None)
                    password = request.POST.get('password', None)
                    if username and password:
                        user = authenticate(username=username, password=password)
                        login(request, user)

                        request.true_id.user = user
                        request.true_id.save()

                        return HttpResponseRedirect(request.META['PATH_INFO'])
                register_form = forms.RegisterForm()
            elif request.POST.get('submit', '') == 'Rekisteröidy':
                register_form = forms.RegisterForm(data)
                if register_form.is_valid():
                    user = register_form.save()

                    username = register_form.cleaned_data['reg_username']
                    password = register_form.cleaned_data['reg_password']
                    user = authenticate(username=username, password=password)
                    login(request, user)

                    request.true_id.user = user
                    request.true_id.save()

                    return HttpResponseRedirect(request.META['PATH_INFO'])
                login_form = forms.LoginForm()
            else:
                register_form = forms.RegisterForm()
                login_form = forms.LoginForm()

            req_ctx['login_form'] = login_form
            req_ctx['register_form'] = register_form
        elif not request.user.id:
            req_ctx['login_form'] = forms.LoginForm()
            req_ctx['register_form'] = forms.RegisterForm()
        else:
            req_ctx['login_form'] = None
            req_ctx['register_form'] = None

        return func(*args, **kwargs)
    return wrap

def dec_true_id_in(func):
    """Check before calling view function if we have a true id
    """

    def wrap(*args, **kwargs):
        request = args[0]

        if not request.COOKIES.has_key('true_id'):
            true_id = sha.sha('%s|%s|%s' % (datetime.datetime.now().isoformat(), datetime.datetime.now().microsecond, datetime.datetime.now().microsecond)).hexdigest()
        else:
            true_id = request.COOKIES['true_id']

        true_id_ob, created = models.TrueId.objects.get_or_create(hash=true_id)

        request.true_id = true_id_ob

        return func(*args, **kwargs)

    return wrap

def dec_true_id_out(func):
    """true_id is our better-than-session cookie
    """

    def wrap(*args, **kwargs):
        req_ctx = args[1]
        request = req_ctx['request']
        response = func(*args, **kwargs)
        if not request.COOKIES.has_key('true_id'):
            true_id_ob = request.true_id
            response.set_cookie('true_id', true_id_ob.hash, max_age=(2**32)-1, domain=settings.COOKIE_DOMAIN)

        return response

    return wrap

render_to_response = dec_login(render_to_response)
render_to_response = dec_true_id_out(render_to_response)

# Create your views here.

def forgot_password(request):
    """I forgot my password
    """

    if request.user.id:
        return HttpResponseRedirect('/')

    data = request.POST.copy() or None
    request_reset_form = forms.RequestResetForm(data)

    if request_reset_form.is_bound:
        if request_reset_form.is_valid():
            token = request_reset_form.save()

            mail_context = {
                'token': token,
                'path': reverse('reset_password', args=(token,)),
            }
            mail_req_context = RequestContext(request, mail_context)

            s = template.loader.get_template('mail/reset_password_url.txt')
            content = s.render(mail_req_context)

            subj = FORGOT_PASSWORD_SUBJECT
            from_email = settings.DEFAULT_FROM_EMAIL
            to_list = (request_reset_form.data['user'].email,)
            mail.send_mail(subj, content, from_email, to_list)

    context = {
        'request_reset_form': request_reset_form,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('forgot_password.html', req_ctx)

def reset_password(request, token):
    """I want to reset my password
    """

    try:
        token_ob = models.ResetRequest.objects.filter(token=token, reset_at__isnull=True).select_related(depth=1)[0]
    except IndexError:
        return HttpResponseRedirect('/')

    if request.user.id:
        return HttpResponseRedirect('/')

    user = token_ob.user

    data = request.POST.copy() or None
    password_reset_form = forms.PasswordResetForm(data)
    if password_reset_form.is_bound:
        if password_reset_form.is_valid():
            new_pass = password_reset_form.cleaned_data['new_password']
            user.set_password(new_pass)
            user.save()

            token_ob.reset_from_ip = request.META['REMOTE_ADDR']
            token_ob.reset_at = datetime.datetime.now()
            token_ob.save()

            # To set backend attribute
            user = authenticate(username=user.username, password=new_pass)
            login(request, user)

            return HttpResponseRedirect('/')

    context = {
        'password_reset_form': password_reset_form,
        'token': token,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('reset_password.html', req_ctx)

def logout_view(request):
    """Logout
    """

    prev_path = request.GET.get('prev_path', '/')
    logout(request)

    request.true_id.user = None
    request.true_id.save()

    return HttpResponseRedirect(prev_path)

def notfound(request):
    """Not found view
    """

    context = {
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('404.html', req_ctx)

@dec_true_id_in
def index(request):
    """Our index page
    """

    data = request.POST.copy() or None
    if data:
        if data['submit'] != 'Lisää':
            data = None
        else:
            data['user'] = request.user

    submit_prkl_form = forms.SubmitPrklForm(data)

    if submit_prkl_form.is_bound:
        if submit_prkl_form.is_valid():
            submit_prkl_form.save()
            
            return HttpResponseRedirect(request.META['PATH_INFO'])

    # FIXME: Django and OUTER JOINs :(
    # There is no way to emulate an OUTER JOIN in a subquery or anything
    prkls = models.Prkl.objects.all().order_by('-created_at')

    context = {
        'title': 'Etusivu',
        'form': submit_prkl_form,
        'prkls': prkls,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)


@dec_true_id_in
def top(request):
    """The best
    """

    # FIXME: Django and OUTER JOINs :(
    # There is no way to emulate an OUTER JOIN in a subquery or anything
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

@dec_true_id_in
def bottom(request):
    """The worst
    """

    # FIXME: Django and OUTER JOINs :(
    # There is no way to emulate an OUTER JOIN in a subquery or anything
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

