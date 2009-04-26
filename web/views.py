# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import models as auth_models

from django.core.urlresolvers import reverse

from django.db.transaction import commit_on_success

from fad_tools.pagination.utils import get_paginator_context

from django.conf import settings

from django.core import mail

from django.http import HttpResponseRedirect
from django.http import HttpResponse

from django.shortcuts import render_to_response

from django.template import RequestContext

from django.utils import simplejson

from fad_tools.messager import models as messager_models

from django import forms as django_forms

from django import template

from web import forms, models
from web import utils
from web import prkl_sql_ob

import datetime

import itertools

import sha

FORGOT_PASSWORD_SUBJECT = 'prkl.es: salasanan vaihto'
INVITE_FRIEND_SUBJECT = 'Kutsu prkl.es -sivustolle!'
CONFIRM_REGISTRATION_SUBJECT = 'Tänään rekisteröidyit prkleeseen prkl'

CAT_REG = 'registration'

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
                    #user = authenticate(username=username, password=password)
                    #login(request, user)

                    #request.true_id.user = user
                    #request.true_id.save()

                    msg = messager_models.Message.objects.create(content='Sähköpostiisi on lähetetty vahvistusviesti!')
                    request.true_id.messageattribute_set.create(message=msg, category=CAT_REG)

                    reg_token = utils.gen_reg_token(request.true_id, username)

                    # Pend
                    pend_reg = models.PendingRegistration()
                    pend_reg.token = reg_token
                    pend_reg.user = user
                    pend_reg.trueid = request.true_id
                    pend_reg.from_ip = request.META['REMOTE_ADDR']
                    pend_reg.save()

                    # Send email
                    mail_context = {
                        'reg_token': reg_token,
                    }
                    mail_req_context = RequestContext(request, mail_context)

                    s = template.loader.get_template('mail/confirm_registration.txt')
                    content = s.render(mail_req_context)

                    subj = CONFIRM_REGISTRATION_SUBJECT
                    from_email = settings.DEFAULT_FROM_EMAIL
                    to_list = (register_form.cleaned_data['reg_email'],)
                    mail.send_mail(subj, content, from_email, to_list)

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

        # Hurts...
        try:
            reg_msg = messager_models.Message.objects.filter(trueid=request.true_id, messageattribute__category='registration', messageattribute__read_at__isnull=True).order_by('-id')[0]
            reg_msg.messageattribute_set.update(read_at=datetime.datetime.now())
            reg_msg.save()
        except IndexError:
            reg_msg = None

        req_ctx['reg_msg'] = reg_msg

        return func(*args, **kwargs)
    return wrap

def dec_true_id_in(func):
    """Check before calling view function if we have a true id
    """

    def _gen_true_id():
        """Something more random would be nice
        """

        true_id = sha.sha('%s|%s|%s' % (datetime.datetime.now().isoformat(), datetime.datetime.now().microsecond, datetime.datetime.now().microsecond)).hexdigest()

        return true_id

    def wrap(*args, **kwargs):
        request = args[0]

        # Did we just fake an entry in cookies?
        request.META['unreal_true_id'] = False
        request.has_session = (request.session.session_key == request.COOKIES.get('sessionid', ''))
        if not request.COOKIES.has_key('true_id'):
            true_id = _gen_true_id()
            true_id_ob = models.TrueId.objects.create(hash=true_id)
            # Cookies are denied, label this fake true_id as fake
            if not request.has_session:
                request.META['unreal_true_id'] = True
                request.COOKIES['true_id'] = true_id
            else:
                response = HttpResponseRedirect(request.META['PATH_INFO'])
                response.set_cookie('true_id', true_id_ob.hash, max_age=(2**32)-1, domain=settings.COOKIE_DOMAIN)
                return response
        else:
            true_id = request.COOKIES['true_id']

            try:
                true_id_ob = models.TrueId.objects.get(hash=true_id)
            except models.TrueId.DoesNotExist:
                # Just to be sure we didn't get tampered, recreate the id
                true_id = _gen_true_id()
                request.META['unreal_true_id'] = True
                true_id_ob = models.TrueId.objects.create(hash=true_id)

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
        if not request.COOKIES.has_key('true_id') or (request.COOKIES.has_key('true_id') and request.META.get('unreal_true_id', False)):
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

def dec_recommend_vip(func):
    """Decorate vip-only pages
    """

    def wrap(*args, **kwargs):
        request = args[0]

        if not request.user.id:
            return dec_recommend_register(func)(*args, **kwargs)

        if not request.user.is_vip:
            context = {
                'title': 'Vain vipeille :(',
            }
            req_ctx = RequestContext(request, context)

            return render_to_response('only_vip.html', req_ctx)

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

def register(request, token):
    if not request.user.id:
        user = authenticate(token=token)
        if user:
            login(request, user)

    return HttpResponseRedirect(reverse('index'))

@dec_true_id_in
def logout_view(request):
    """Logout
    """

    prev_path = request.GET.get('prev_path', '/')
    logout(request)

    request.true_id.user = None
    request.true_id.save()

    return HttpResponseRedirect(prev_path)

@dec_true_id_in
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
def about_vip(request):
    """VIP information
    """

    context = {
        'title': 'vip-tietoa',
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('about_vip.html', req_ctx)

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

    tags = models.Tag.objects.filter(is_default=True).values('id', 'name')
    tags = [(t['id'], t['name']) for t in tags]
    submit_prkl_form.fields['tags'].choices = tags

    if request.user.id:
        checkbox = django_forms.BooleanField(label='Anonyymisti?', required=False)
        submit_prkl_form.fields['anonymous'] = checkbox

    if submit_prkl_form.is_bound:
        if submit_prkl_form.is_valid():
            request.true_id.visible_prklform = False
            request.true_id.save()

            submit_prkl_form.save()

            return HttpResponseRedirect(request.META['PATH_INFO'])

    ### Was 27 queries 70.39ms for index
    ### Now 7 queries in 41ms for index
    if request.user.id:
        prkls = prkl_sql_ob.PrklQuery(vote_userid=request.user.id, like_userid=request.user.id)
    else:
        prkls = prkl_sql_ob.PrklQuery(vote_trueid=request.true_id)

    if not request.has_session or request.META['unreal_true_id']:
        prkls.disable_votes()

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
        'submit_prkl_form': submit_prkl_form,
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

    # Get prkls
    if request.user.id:
        prkls = prkl_sql_ob.PrklQuery(vote_userid=request.user.id, like_userid=request.user.id)
    else:
        prkls = prkl_sql_ob.PrklQuery(vote_trueid=request.true_id)

    if not request.has_session or request.META['unreal_true_id']:
        prkls.disable_votes()

    # order
    prkls.top()

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

    # Get prkls
    if request.user.id:
        prkls = prkl_sql_ob.PrklQuery(vote_userid=request.user.id, like_userid=request.user.id)
    else:
        prkls = prkl_sql_ob.PrklQuery(vote_trueid=request.true_id)

    if not request.has_session or request.META['unreal_true_id']:
        prkls.disable_votes()

    # order
    prkls.bottom()

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

    # First off, see where we're returned
    if back_to is None:
        back_to = '/'
    else:
        back_to = '/%s' % back_to

    # And if we don't have a cookie, bail out
    if not request.COOKIES.has_key('true_id'):
        return HttpResponseRedirect(back_to)

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
        if not request.has_session or request.META['unreal_true_id']:
            prkl = prkl.disable_votes()
        else:
            prkl = prkl.can_vote(your_votes)
        prkl = prkl[0]
    except IndexError:
        return notfound(request)

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

    member_likes = models.Prkl.objects.filter(prkllike__user=member).order_by('?')
    if request.user.id:
        your_likes = models.Prkl.objects.filter(prkllike__user=request.user)
        member_likes = member_likes.does_like(your_likes)

    if member.is_vip and request.user == member:
        liked_prkls = models.Prkl.objects.filter(prkllike__prkl__user=member)
        # And liking statuses
        if request.user.id:
            your_likes = models.Prkl.objects.filter(prkllike__user=request.user)
            liked_prkls = liked_prkls.does_like(your_likes)
            liked_prkls = liked_prkls.distinct()
    else:
        liked_prkls = None

    context = {
        'title': '%s' % username,
        'member': member,
        'change_pic_form': change_pic_form,
        'liked_prkls': liked_prkls,
        'member_likes': member_likes,
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

    # Affect css
    css_ctx = {
        'css_paginator': 'members_paginator',
    }

    pag_ctx = get_paginator_context(members, page, records, def_ctx=css_ctx)

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
    initial_profile = {
        'location': request.user.location,
        'birthday': request.user.birthday,
    }
    initial_desc = {
        'description': request.user.description
    }

    if request.user.is_male is None:
        initial_profile['sex'] = 1
    elif request.user.is_male:
        initial_profile['sex'] = 2
    else:
        initial_profile['sex'] = 3

    if request.GET.get('rm_pic', None) and request.user.pic:
        request.user.pic.delete()

    ## This is inoptimal, it deals in description form without checking vip
    if data and data['submit'] == 'Päivitä':
        change_pic_form = forms.ChangePicForm(data, files=request.FILES)
        edit_profile_form = forms.EditProfileForm(initial=initial_profile)
        edit_description_form = forms.EditDescriptionForm(initial_desc)
    elif data and data['submit'] == 'Muokkaa':
        change_pic_form = forms.ChangePicForm()
        edit_profile_form = forms.EditProfileForm(data, initial=initial_profile)
        edit_description_form = forms.EditDescriptionForm(data, initial_desc)
    else:
        change_pic_form = forms.ChangePicForm()
        edit_profile_form = forms.EditProfileForm(initial=initial_profile)
        edit_description_form = forms.EditDescriptionForm(initial=initial_desc)

    if change_pic_form.is_bound:
        if change_pic_form.is_valid():
            change_pic_form.data['user'] = request.user
            change_pic_form.save()

            return HttpResponseRedirect(request.META['PATH_INFO'])

    if edit_profile_form.is_bound or (edit_description_form.is_bound and request.user.is_vip):
        if edit_profile_form.is_bound and edit_profile_form.is_valid():
            edit_profile_form.data['user'] = request.user
            edit_profile_form.save()

        if edit_description_form.is_bound and edit_description_form.is_valid() and request.user.is_vip:
            edit_description_form.data['user'] = request.user
            edit_description_form.save()

        return HttpResponseRedirect(reverse('member', args=(request.user.username,)))

    context = {
        'title': 'Profiilin editointi',
        'member': request.user,
        'change_pic_form': change_pic_form,
        'edit_description_form': edit_description_form,
        'edit_profile_form': edit_profile_form,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('edit_profile.html', req_ctx)

def init_json_ctx(request, data):
    """Helper for dealing with initing json and stuff
    request is the obvious object, but data is separete because of GET or POST
    """

    # By default, don't cause the view to bail out
    good = True

    # Always see if we're even slightly valid
    true_id = data.get('h', '')

    context = {
        'status': 'NOK',
        'message': 'No request',
        'errors': ('No request',)
    }

    if request.true_id.hash != true_id:
        context['message'] = 'Value mismatch'
        context['errors'] = ('Value mismatch',)

        good = False

    try:
        true_id_ob = models.TrueId.objects.get(hash=true_id)
    except models.TrueId.DoesNotExist, msg:
        true_id_ob = None
        #msg = '%s (%s)' % (msg, true_id)
        context['message'] = 'Not found'
        context['errors'] = (str(msg),)
        #context['errors'] = (msg,)

        good = False

    return context, true_id_ob, good


@dec_true_id_in
def set_form_visibility(request):
    """Semi-api view for dealing with visibilities
    """

    form = request.POST.get('f', '')
    visibility = request.POST.get('v', '')

    context, true_id_ob, good = init_json_ctx(request, request.POST)
    if not good:
        ctx = simplejson.dumps(context)

        return HttpResponse(ctx, content_type='text/json')

    if form == 'prklform':
        if visibility == 'true':
            true_id_ob.visible_prklform = True
        else:
            true_id_ob.visible_prklform = False

        true_id_ob.save()

        context['status'] = 'OK'
        context['message'] = 'Updated'
        context['errors'] = None

    elif form == 'regform':
        if visibility == 'true':
            true_id_ob.visible_regform = True
        else:
            true_id_ob.visible_regform = False

        true_id_ob.save()

        context['status'] = 'OK'
        context['message'] = 'Updated'
        context['errors'] = None
    else:
        context['message'] = 'Bad form'
        context['errors'] = ('Bad form',)

    ctx = simplejson.dumps(context)

    return HttpResponse(ctx, content_type='text/json')
    
@dec_true_id_in
@dec_recommend_vip
def search(request, page=None, records=None):
    """Detailed search
    """

    data = request.GET.copy() or None

    initial = {
        'sex': '4',
    }

    result = None
    user_search_form = forms.UserSearchForm(data, initial=initial)
    if user_search_form.is_bound:
        if user_search_form.is_valid():
            result = user_search_form.search()

    # Pagination
    if not page:
        page = 1
    page = int(page)

    if not records:
        records = 5
    records = int(records)

    # Affect css
    css_ctx = {
        'css_paginator': 'members_paginator',
    }

    prkl_count_dict = {}
    if result:
        pag_ctx = get_paginator_context(result, page, records, def_ctx=css_ctx)

        # Prkl counts
        shown = pag_ctx['page_objects'].object_list

        prkl_counts = models.Prkl.objects.filter(user__id__in=[u.id for u in shown])
        prkl_counts = prkl_counts.extra(tables=('auth_user',), where=('web_prkl.user_id=auth_user.id',), select={
            'username': 'auth_user.username',
        })
        prkl_counts = prkl_counts.order_by('user')
        for group, prkls in itertools.groupby(prkl_counts, lambda x: x.username):
            prkl_count_dict[group] = len(list(prkls))

    context = {
        'title': 'Haku',
        'user_search_form': user_search_form,
        'prkl_count_dict': prkl_count_dict,
    }
    if result:
        context.update(pag_ctx)
    req_ctx = RequestContext(request, context)

    return render_to_response('search.html', req_ctx)

@dec_true_id_in
@dec_recommend_register
def msg_to_user(request, rcpt):
    """Send a message to user
    """

    try:
        member = models.User.objects.get(username__iexact=rcpt)
    except models.User.DoesNotExist:
        return notfound(request)

    your_sent = request.user.sent_messages.filter(recipient__user_ptr=member).order_by('-sent_at')

    data = request.POST.copy() or None

    msg_to_user_form = forms.MsgToUserForm(data)

    if msg_to_user_form.is_bound:
        if msg_to_user_form.is_valid():
            # Traditionally smuggle data
            msg_to_user_form.data['sender'] = request.user
            msg_to_user_form.data['recipient'] = member
            msg_to_user_form.save()

            return HttpResponseRedirect(request.META['PATH_INFO'])

    context = {
        'title': 'Viestiä käyttäjälle %s' % rcpt,
        'member': member,
        'your_sent': your_sent,
        'msg_to_user_form': msg_to_user_form,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('msg_to_user.html', req_ctx)

@dec_true_id_in
@dec_recommend_register
def user_inbox(request):
    """Incoming messages
    """

    messages = models.PrivMessage.objects.inbox(request.user)

    for i in xrange(len(messages)):
        initial = {
            'in_reply_to': messages[i].id,
        }
        messages[i].reply_form = forms.ReplyForm(initial=initial, prefix=str(messages[i].id))
        messages[i].reply_form.fields['in_reply_to'].initial = messages[i].id
        messages[i].reply_form.fields['prefix'].initial = messages[i].id

    context = {
        'title': 'Saapuneet viestisi',
        'inbox_messages': messages,
        'member': request.user,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('user_inbox.html', req_ctx)

@dec_true_id_in
@dec_recommend_register
def user_sent(request):
    """Sent messages
    """

    messages = models.PrivMessage.objects.sent(request.user)

    """
    for i in xrange(len(messages)):
        initial = {
            'in_reply_to': messages[i].id,
        }
        messages[i].reply_form = forms.ReplyForm(initial=initial, prefix=str(messages[i].id))
        messages[i].reply_form.fields['in_reply_to'].initial = messages[i].id
        messages[i].reply_form.fields['prefix'].initial = messages[i].id
    """

    context = {
        'title': 'Lähettämäsi viestit',
        'sent_messages': messages,
        'member': request.user,
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('user_sent.html', req_ctx)


@dec_true_id_in
def mark_msg_read(request):
    """Mark a message you received read
    """

    context, true_id_ob, good = init_json_ctx(request, request.POST)
    if not good:
        ctx = simplejson.dumps(context)

        return HttpResponse(ctx, content_type='text/json')

    message = models.PrivMessage.objects.inbox(request.user)
    message = message.filter(read_at__isnull=True)
    message = message.filter(recipient=request.user)
    try:
        message = message[0]
        message.mark_read()
        context = {
            'status': 'OK',
            'message': 'Marked read',
            'errors': None,
        }
    except IndexError:
        context = {
            'status': 'NOK',
            'message': 'No message',
            'errors': ('No message',)
        }

    ctx = simplejson.dumps(context)

    return HttpResponse(ctx, content_type='text/json')


@dec_true_id_in
def post_reply(request):
    """Reply to a message
    """

    context, true_id_ob, good = init_json_ctx(request, request.POST)
    if not good:
        ctx = simplejson.dumps(context)

        return HttpResponse(ctx, content_type='text/json')

    data = request.POST.copy() or None

    # Deal with prefix
    if data:
        prefix = None
        for key, value in data.items():
            if key.endswith('prefix'):
                prefix = value
                break

        if prefix:
            for key, value in data.items():
                if key.startswith(prefix):
                    non_prefixed = key.rsplit('-', 1)[-1]
                    data[non_prefixed] = value
                    del data[key]

    reply_form = forms.ReplyForm(data=data)

    if reply_form.is_bound:
        # Smuggle in user to validate in_reply_to
        reply_form.data['user'] = request.user
        if reply_form.is_valid():
            msg = reply_form.save()
            context['data'] = {
                'id': msg.id,
                'in_reply_to': msg.parent_id,
            }
            context['status'] = 'OK'
            context['message'] = 'Posted'
            context['errors'] = None
        else:
            context['message'] = 'invalid data'
            context['errors'] = [str(e) for e in reply_form.errors]
    else:
        context['message'] = 'Empty data'

    ctx = simplejson.dumps(context)

    return HttpResponse(ctx, content_type='text/json')

# EOF

