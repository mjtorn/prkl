# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import models as auth_models

from django.core.urlresolvers import reverse

from django.db.transaction import commit_on_success

from fad_tools.pagination.utils import get_paginator_context

from django.conf import settings

from django.core import mail

from django.http import HttpResponseRedirect

from django.shortcuts import render_to_response

from django.template import RequestContext

from django import forms as django_forms

from django import template

from web import forms, models

import datetime

import itertools

import sha

FORGOT_PASSWORD_SUBJECT = 'prkl.es: salasanan vaihto'
INVITE_FRIEND_SUBJECT = 'Kutsu prkl.es -sivustolle!'

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

            # But support inviting friends
            if request.POST.get('submit', '') == 'Kutsu':
                invite_friend_form = forms.InviteFriendForm(data)
                if invite_friend_form.is_valid():
                    invite_friend_form.data['user'] = request.user
                    invite_friend_form.save()

                    # Send email
                    mail_context = {
                        'user': request.user,
                    }
                    mail_req_context = RequestContext(request, mail_context)

                    s = template.loader.get_template('mail/invite_friend.txt')
                    content = s.render(mail_req_context)

                    subj = INVITE_FRIEND_SUBJECT
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to_list = (invite_friend_form.cleaned_data['invitee_email'],)
                    mail.send_mail(subj, content, from_email, to_list)

                    # Set web status
                    req_ctx['invite_result'] = 'Kutsuttu!'
            else:
                invite_friend_form = forms.InviteFriendForm()
            req_ctx['invite_friend_form'] = invite_friend_form

        if not req_ctx.has_key('title') or not req_ctx['title']:
            raise ValueError('Title needed')

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
            if not hasattr(request, 'true_id'):
                true_id = sha.sha('%s|%s|%s' % (datetime.datetime.now().isoformat(), datetime.datetime.now().microsecond, datetime.datetime.now().microsecond)).hexdigest()
                true_id_ob, created = models.TrueId.objects.get_or_create(hash=true_id)
            else:
                true_id_ob = request.true_id

            response.set_cookie('true_id', true_id_ob.hash, max_age=(2**32)-1, domain=settings.COOKIE_DOMAIN)

        return response

    return wrap

def dec_recommend_register(func):
    """Decorate member-only pages
    """

    def wrap(*args, **kwargs):
        request = args[0]

        if not request.user.id:
            context = {
                'title': 'Vain rekisteröityneille :(',
            }
            req_ctx = RequestContext(request, context)

            return render_to_response('only_registered.html', req_ctx)

        return func(*args, **kwargs)
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
        'title': 'Salasanan unohdus',
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
        'title': 'Salasanan vaihto',
        'password_reset_form': password_reset_form,
        'token': token,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('reset_password.html', req_ctx)

@dec_true_id_in
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
        'title': 'Tänään ei löytyny, prkl',
    }
    req_ctx = RequestContext(request, context)

    res = render_to_response('404.html', req_ctx)
    res.status_code = 404
    return res

@dec_true_id_in
def index(request, page=None, records=None):
    """Our index page
    """

    mark_intro = request.GET.get('mark_intro', None)
    if mark_intro:
        request.true_id.mark_seen_intro()
        return HttpResponseRedirect(request.META['PATH_INFO'])

    data = request.POST.copy() or None
    if data:
        if data['submit'] != 'Lisää':
            data = None
        else:
            data['user'] = request.user

    submit_prkl_form = forms.SubmitPrklForm(data)

    if request.user.id:
        checkbox = django_forms.BooleanField(label='Anonyymisti?', required=False)
        submit_prkl_form.fields['anonymous'] = checkbox

    if submit_prkl_form.is_bound:
        if submit_prkl_form.is_valid():
            submit_prkl_form.save()
            
            return HttpResponseRedirect(request.META['PATH_INFO'])

    # FIXME: Django and OUTER JOINs :(
    # There is no way to emulate an OUTER JOIN in a subquery or anything
    your_votes = models.PrklVote.objects.your_votes(request)

    # Include vote statuses
    prkls = models.Prkl.objects.all()
    prkls = prkls.can_vote(your_votes)

    # And liking statuses
    if request.user.id:
        your_likes = models.Prkl.objects.filter(prkllike__user=request.user)
        prkls = prkls.does_like(your_likes)

    prkls = prkls.order_by('-created_at')

    # Pagination
    if not page:
        page = 1
    page = int(page)

    if not records:
        records = 10
    records = int(records)

    pag_ctx = get_paginator_context(prkls, page, records)

    context = {
        'title': 'Etusivu',
        'form': submit_prkl_form,
        'prkls': prkls,
        'base_url': 'http://%s' % request.META['HTTP_HOST'],
    }
    context.update(pag_ctx)
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)


@dec_true_id_in
def top(request, page=None, records=None):
    """The best
    """

    # FIXME: Django and OUTER JOINs :(
    # There is no way to emulate an OUTER JOIN in a subquery or anything
    your_votes = models.PrklVote.objects.your_votes(request)
    prkls = models.Prkl.objects.all()
    prkls = prkls.can_vote(your_votes)
    prkls = prkls.order_by('-score', 'created_at')

    # And liking statuses
    if request.user.id:
        your_likes = models.Prkl.objects.filter(prkllike__user=request.user)
        prkls = prkls.does_like(your_likes)

    # Pagination
    if not page:
        page = 1
    page = int(page)

    if not records:
        records = 10
    records = int(records)

    pag_ctx = get_paginator_context(prkls, page, records)

    context = {
        'title': 'Parhaat',
        'prkls': prkls,
        'base_url': reverse('top'),
    }
    context.update(pag_ctx)
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)

@dec_true_id_in
def bottom(request, page=None, records=None):
    """The worst
    """

    # FIXME: Django and OUTER JOINs :(
    # There is no way to emulate an OUTER JOIN in a subquery or anything
    your_votes = models.PrklVote.objects.your_votes(request)
    prkls = models.Prkl.objects.all()
    prkls = prkls.can_vote(your_votes)
    prkls = prkls.order_by('score', '-created_at')

    # And liking statuses
    if request.user.id:
        your_likes = models.Prkl.objects.filter(prkllike__user=request.user)
        prkls = prkls.does_like(your_likes)

    # Pagination
    if not page:
        page = 1
    page = int(page)

    if not records:
        records = 10
    records = int(records)
    pag_ctx = get_paginator_context(prkls, page, records)

    context = {
        'title': 'Huonoimmat',
        'prkls': prkls,
        'base_url': reverse('bottom'),
    }
    context.update(pag_ctx)
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)

@commit_on_success
@dec_true_id_in
def vote(request, prkl_id, direction, back_to):
    """And I found direction...
    """

    your_votes = models.PrklVote.objects.your_votes(request)
    prkls = models.Prkl.objects.all()
    prkls = prkls.can_vote(your_votes)

    good = False
    try:
        prkl = prkls.get(id=prkl_id)
        if prkl.can_vote:
            good = True
    except models.Prkl.DoesNotExist:
        pass

    if back_to is None:
        back_to = '/'
    else:
        back_to = '/%s' % back_to

    if not good:
        return HttpResponseRedirect(back_to)

    vote = models.PrklVote()
    if request.user.id:
        vote.user = request.user
    else:
        vote.trueid = request.true_id

    # Pre-validated in urls.py
    if direction == 'up':
        prkl.incr()
        vote.vote = 1
    else:
        prkl.decr()
        vote.vote = -1

    vote.prkl = prkl
    vote.save()

    return HttpResponseRedirect(back_to)

@commit_on_success
@dec_true_id_in
@dec_recommend_register
def like(request, prkl_id, action, back_to):
    """Do you like this prkl?
    """

    if not back_to:
        back_to = '/'
    else:
        back_to = '/%s' % back_to

    if action == 'yes':
        try:
            prkl_like = models.PrklLike.objects.get(prkl__id=prkl_id, user=request.user)
        except models.PrklLike.DoesNotExist:
            try:
                prkl = models.Prkl.objects.get(id=prkl_id)
                prkl_like = models.PrklLike()
                prkl_like.prkl = prkl
                prkl_like.user = request.user
                prkl_like.save()
            except models.Prkl.DoesNotExist:
                pass
    else:
        your_likes = models.PrklLike.objects.filter(prkl__id=prkl_id, user=request.user).delete()

    return HttpResponseRedirect(back_to)

@dec_true_id_in
def prkl(request, prkl_id):
    """Single-prkl view
    """

    your_votes = models.PrklVote.objects.your_votes(request)
    try:
        prkl = models.Prkl.objects.filter(id= prkl_id)
        prkl = prkl.can_vote(your_votes)
        prkl = prkl[0]
    except IndexError:
        return HttpResponseNotFound()

    comments = prkl.prklcomment_set.all().order_by('tstamp')

    data = request.POST.copy() or None

    if data:
        button = data.get('submit', '')
        if button == 'Kommentoi':
            comment_prkl_form = forms.CommentPrklForm(data)
            if comment_prkl_form.is_bound:
                if comment_prkl_form.is_valid():
                    comment_prkl_form.data['prkl'] = prkl
                    comment_prkl_form.data['user'] = request.user
                    comment_prkl_form.save()

                    return HttpResponseRedirect(request.META['PATH_INFO'])
        else:
            comment_prkl_form = forms.CommentPrklForm()
    else:
        comment_prkl_form = forms.CommentPrklForm()

    context = {
        'title': 'Yksittäinen prkl',
        'prkl': prkl,
        'comments': comments,
        'comment_prkl_form': comment_prkl_form,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('prkl.html', req_ctx)

@dec_true_id_in
@dec_recommend_register
def member(request, username):
    try:
        member = models.User.objects.get(username__iexact=username)
    except models.User.DoesNotExist:
        return notfound(request)

    data = request.POST.copy() or None

    if member.id == request.user.id and request.user.is_vip:
        if request.GET.get('rm_pic', None) and member.pic:
            member.pic.delete()
        if data:
            change_pic_form = forms.ChangePicForm(data, files=request.FILES)
        else:
            change_pic_form = forms.ChangePicForm()

        if change_pic_form.is_bound:
            if change_pic_form.is_valid():
                change_pic_form.data['user'] = request.user
                change_pic_form.save()

                return HttpResponseRedirect(request.META['PATH_INFO'])
    else:
        change_pic_form = None

    if member.is_vip:
        member_prkls = member.prkl_set.all().order_by('-score', 'created_at')
        # And liking statuses
        if request.user.id:
            your_likes = models.Prkl.objects.filter(prkllike__user=request.user)
            member_prkls = member_prkls.does_like(your_likes)

    else:
        member_prkls = None

    context = {
        'title': '%s' % username,
        'member': member,
        'change_pic_form': change_pic_form,
        'member_prkls': member_prkls,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('member.html', req_ctx)

@dec_true_id_in
@dec_recommend_register
def members(request, page=None, records=None):
    data = request.GET.copy() or None

    find_friend = None
    find_friend_form = forms.FindFriendForm(data)
    if find_friend_form.is_bound and find_friend_form.is_valid():
        find_friend = find_friend_form.cleaned_data['find_friend']
        if find_friend:
            members = models.User.objects.search(find_friend, order_by=('username',))
        else:
            members = models.User.objects.all().order_by('-date_joined')
    else:
        members = models.User.objects.all().order_by('-date_joined')

    # Pagination
    if not page:
        page = 1
    page = int(page)

    if not records:
        records = 5
    records = int(records)
    pag_ctx = get_paginator_context(members, page, records)

    # Prkl counts
    shown = pag_ctx['page_objects'].object_list
    prkl_counts = models.Prkl.objects.filter(user__id__in=[u.id for u in shown])
    prkl_counts = prkl_counts.extra(tables=('auth_user',), where=('web_prkl.user_id=auth_user.id',), select={
        'username': 'auth_user.username',
    })
    prkl_counts = prkl_counts.order_by('user')
    prkl_count_dict = {}
    for group, prkls in itertools.groupby(prkl_counts, lambda x: x.username):
        prkl_count_dict[group] = len(list(prkls))

    context = {
        'title': 'Jäsenlista',
        'members': members,
        'find_friend': find_friend,
        'find_friend_form': find_friend_form,
        'prkl_count_dict': prkl_count_dict,
        'members_page': True,
    }
    context.update(pag_ctx)
    req_ctx = RequestContext(request, context)

    return render_to_response('members.html', req_ctx)



@dec_true_id_in
@dec_recommend_register
def edit_profile(request):
    # ADAPT FROM MEMBER VIEW
    data = request.POST.copy() or None

    # But also user info edit
    initial = {
        'location': request.user.location,
        'birthday': request.user.birthday,
    }
    if request.user.is_male is None:
        initial['sex'] = 1
    elif request.user.is_male:
        initial['sex'] = 2
    else:
        initial['sex'] = 3

    if request.GET.get('rm_pic', None) and request.user.pic:
        request.user.pic.delete()

    if data and data['submit'] == 'Päivitä':
        change_pic_form = forms.ChangePicForm(data, files=request.FILES)
        edit_profile_form = forms.EditProfileForm(initial=initial)
    elif data and data['submit'] == 'Muokkaa':
        change_pic_form = forms.ChangePicForm()
        edit_profile_form = forms.EditProfileForm(data, initial=initial)
    else:
        change_pic_form = forms.ChangePicForm()
        edit_profile_form = forms.EditProfileForm(initial=initial)

    if change_pic_form.is_bound:
        if change_pic_form.is_valid():
            change_pic_form.data['user'] = request.user
            change_pic_form.save()

            return HttpResponseRedirect(request.META['PATH_INFO'])

    if edit_profile_form.is_bound:
        if edit_profile_form.is_valid():
            edit_profile_form.data['user'] = request.user
            edit_profile_form.save()
            return HttpResponseRedirect(reverse('member', args=(request.user.username,)))

    context = {
        'title': 'Profiilin editointi',
        'member': request.user,
        'change_pic_form': change_pic_form,
        'edit_profile_form': edit_profile_form,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('edit_profile.html', req_ctx)

    

# EOF

