# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate
from django.contrib.auth import models as auth_models
from django.contrib.auth import tokens

from django.db.transaction import commit_on_success

from django.utils.html import conditional_escape, force_unicode

from django.utils.safestring import mark_safe

from django import forms

from web import models

import datetime

## SuperClass Me (harder)

class PrklErrorField(forms.util.ErrorList):
    def __unicode__(self):
        return self.as_prkl()

    def as_prkl(self):
        if not self:
            return ''

        return mark_safe('%s'
            % ''.join([u'%s<br />' % conditional_escape(force_unicode(e)) for e in self]))


class PrklSuperForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs['error_class'] = PrklErrorField
        forms.Form.__init__(self, *args, **kwargs)

    def as_prkl(self):
        # normal_row, error_row, row_ender, help_text_html, errors_on_separate_row
        normal_row = '<p><div>%(label)s</div> <br />%(field)s <br /><span class="error">%(errors)s</span> %(help_text)s '
        error_row = '<span style="color: red;">%s</span>'
        row_ender = '</p>'
        help_text_html = ' %s'
        errors_on_separate_row = False

        return self._html_output(normal_row, error_row, row_ender, help_text_html, errors_on_separate_row)

    def as_prkl_all_req(self):
        # normal_row, error_row, row_ender, help_text_html, errors_on_separate_row
        normal_row = '<p><div><span class="required">*</span>%(label)s</div> <br />%(field)s <br /><span class="error">%(errors)s</span> %(help_text)s '
        error_row = '<span style="color: red;">%s</span>'
        row_ender = '</p>'
        help_text_html = ' %s'
        errors_on_separate_row = False

        return self._html_output(normal_row, error_row, row_ender, help_text_html, errors_on_separate_row)

## Children

class RequestResetForm(PrklSuperForm):
    error_messages = {
        'required': 'Tämä kenttä tarvitaan',
        'invalid': 'Epävalidi sähköpostiosoite',
    }

    email = forms.EmailField(label='Sähköpostisi', error_messages=error_messages)

    def clean_email(self):
        try:
            user = models.User.objects.get(email=self.data['email'])
            self.data['user'] = user
        except models.User.DoesNotExist:
            raise forms.ValidationError('Sähköpostiosoitetta ei löytynyt')

        return self.data['email']

    @commit_on_success
    def save(self):
        # Generate token
        token_generator = tokens.PasswordResetTokenGenerator()

        # Smuggle user again
        user = self.data['user']

        token = token_generator.make_token(user)
        reset_request, created = models.ResetRequest.objects.get_or_create(
            user = user,
            token = token
        )

        return token


class PasswordResetForm(PrklSuperForm):
    error_messages = {
        'required': 'Annathan uuden salasanasi :)'
    }
    new_password = forms.CharField(label='Uusi salasana', error_messages=error_messages, widget=forms.widgets.PasswordInput())


class LoginForm(PrklSuperForm):
    # Localizbation
    error_messages = {
        'required': 'Tämä kenttä tarvitaan',
    }

    # Widget attributes
    attrs = {
        'size': 12,
    }

    username = forms.CharField(label='Tunnus', error_messages=error_messages, widget=forms.widgets.TextInput(attrs=attrs))
    password = forms.CharField(label='Salasana', error_messages=error_messages, widget=forms.widgets.PasswordInput(attrs=attrs))

    def clean_username(self):
        username = self.data.get('username', '').strip()
        password = self.data.get('password', '')

        user = authenticate(username=username, password=password)
        if not user:
            raise forms.ValidationError('Nimi tai salasana väärä')

        return self.data['username']


class RegisterForm(PrklSuperForm):
    # Custom Finnish error messages
    error_messages = {
        'required': 'Tämä kenttä tarvitaan',
        'invalid': 'Epävalidi sähköpostiosoite',
    }

    # Widget attributes
    attrs = {
        'size': 12,
    }

    reg_username = forms.CharField(label='Tunnus', error_messages=error_messages, widget=forms.widgets.TextInput(attrs=attrs))
    reg_password = forms.CharField(label='Salasana', error_messages=error_messages, widget=forms.widgets.PasswordInput(attrs=attrs))
    reg_email = forms.EmailField(label='Sähköposti', error_messages=error_messages, widget=forms.widgets.TextInput(attrs=attrs))

    def clean_reg_username(self):
        username = self.data.get('reg_username', '').strip()

        if not username:
            raise forms.ValidationError('Tunnus tarvitaan')

        exists = (auth_models.User.objects.filter(username__iexact=username).count() > 0)
        if exists:
            raise forms.ValidationError('Tunnus on jo otettu')

        return username

    def clean_reg_email(self):
        email = self.data.get('reg_email', '').strip()
        if not email:
            raise forms.ValidationError('Sähköposti tarvitaan')

        exists = (auth_models.User.objects.filter(email=email).count() > 0)
        if exists:
            raise forms.ValidationError('Sähköposti on jo otettu')

        return email

    @commit_on_success
    def save(self):
        # Create new user
        username = self.cleaned_data['reg_username']
        password = self.cleaned_data['reg_password']
        email = self.cleaned_data['reg_email']
        user = models.User()
        user.username = username
        user.email = email
        # Until the confirmation is in
        user.is_active = False
        user.set_password(password)

        user.save()

        ## Give vip even if registered user doesn't confirm so the inviter doesn't feel screwed
        # Also see if this was an invite
        try:
            invite = models.FriendInvite.objects.get(recipient=email)
            invite.registered_at = datetime.datetime.now()
            user_invite_count = models.FriendInvite.objects.filter(sent_by_user=invite.sent_by_user, registered_at__isnull=False).count()
            if user_invite_count < 6:
                if invite.sent_by_user.is_vip:
                    invite.sent_by_user.extend_vip(datetime.timedelta(days=5))
                else:
                    invite.sent_by_user.set_vip(datetime.datetime.now() + datetime.timedelta(days=5))
            invite.save()
        except models.FriendInvite.DoesNotExist:
            pass
        return user


class SubmitPrklForm(PrklSuperForm):
    content_error_messages = {
        'required': 'Taisi jäädä prkl kirjoittamatta!',
    }
    tag_error_messages = {
        'invalid_choice': 'Tänään vaihtoehto %(value)s ei ole listassa prkl',
        'invalid_list': 'Lista ei ole pätevä',
    }
    attrs = {
        'cols': 55,
        'rows': 3,
    }
    content = forms.CharField(label='Sinun prkleesi', error_messages=content_error_messages, widget=forms.widgets.Textarea(attrs=attrs))
    tags = forms.MultipleChoiceField(label='Tagit', error_messages=tag_error_messages, choices=(), widget=forms.widgets.CheckboxSelectMultiple())

    def clean_content(self):
        content = self.data['content'].strip()

        if not content.lower().startswith('tänään'):
            raise forms.ValidationError('Aloitathan Prkleesi sanalla tänään')

        # FIXME: Allow some amount of . and ! and maybe ? at the end
        if not content.lower().endswith('prkl'):
            raise forms.ValidationError('Päätäthän Prkleesi sanalla prkl')

        return '%s%s' % ('T', content[1:])

    @commit_on_success
    def save(self):
        new_prkl = models.Prkl()
        new_prkl.content = self.cleaned_data['content']
        user = self.data['user']
        if user.id:
            # See if someone set an anonymity here
            if not self.data.has_key('anonymous'):
                new_prkl.user = user
        new_prkl.save()
        new_prkl.tag.add(*self.cleaned_data['tags'])


class CommentPrklForm(PrklSuperForm):
    error_messages = {
        'required': 'Kirjoitathan kommentin!',
    }

    attrs = {
        'rows': 5,
        'cols': 55,
    }

    content = forms.CharField(label='Kommentti', error_messages=error_messages, widget=forms.widgets.Textarea(attrs=attrs))

    def clean_content(self):
        return self.data.get('content', '').strip()

    @commit_on_success
    def save(self):
        prkl_comment = models.PrklComment()

        prkl_comment.prkl = self.data['prkl']
        if self.data['user'].id:
            prkl_comment.commenting_user = self.data['user']
        prkl_comment.content = self.cleaned_data['content']

        prkl_comment.save()


class InviteFriendForm(PrklSuperForm):
    # Error
    error_messages = {
        'invalid': 'Tämä sähköposti ei toimi',
        'required': 'Tämä sähköposti vaaditaan',
    }

    # Widget attributes
    attrs = {
        'size': 12,
    }

    invitee_email = forms.EmailField(label='Sähköposti', error_messages=error_messages, widget=forms.widgets.TextInput(attrs=attrs))

    def clean_invitee_email(self):
        email = self.data.get('invitee_email', '').strip()
        if not email:
            raise forms.ValidationError('Sähköposti tarvitaan')

        exists = (auth_models.User.objects.filter(email=email).count() > 0)
        if exists:
            raise forms.ValidationError('Käyttäjä on jo liittynyt!')

        exists = (models.FriendInvite.objects.filter(recipient=email).count() > 0)
        if exists:
            raise forms.ValidationError('Käyttäjä on jo kutsuttu!')

        return email

    def save(self):
        friend_invite = models.FriendInvite()

        friend_invite.sent_by_user = self.data['user']
        friend_invite.recipient = self.cleaned_data['invitee_email']

        friend_invite.save()

class ChangePicForm(PrklSuperForm):
    error_messages = {
        'required': 'Kuvaa tulee',
        'invalid': 'Kuvassa on jotain vialla',
    }
    pic = forms.ImageField(label='Kuva', error_messages=error_messages)

    @commit_on_success
    def save(self):
        user = self.data['user']
        pic = self.cleaned_data['pic']

        # Rewind
        pic.open()

        if user.pic:
            user.pic.delete()

        user.pic.save(pic.name, pic)
        user.save()

class EditProfileForm(PrklSuperForm):
    loc_errors = {
        'max_length': 'Kerrothan ylläpidolle jos paikkakuntasi ei mahdu 24 merkkiin'
    }

    sex_choices = ((1, 'Ei kerro'), (2, 'Mies'), (3, 'Nainen'))
    sex_errors = {
        'required': 'Valitse edes "Ei kerro"',
        'invalid_choice': 'Tuo ei ole sukupuoli',
    }

    bday_errors = {
        'invalid': 'Tuo ei näytä oikealta päivämäräältä',
    }

    bday_formats = (
        '%Y-%m-%d',
        '%d. %m. %Y',
        '%d.%m. %Y',
        '%d.%m.%Y',
        '%d %m %Y',
    )

    location = forms.CharField(label='Sijainti', max_length=24, required=False, error_messages=loc_errors)
    sex = forms.ChoiceField(label='Sukupuoli', error_messages=sex_errors, choices=sex_choices)
    birthday = forms.DateField(label='Syntymäpäivä', required=False, input_formats=bday_formats, error_messages=bday_errors, widget=forms.widgets.DateTimeInput(format='%d. %m. %Y'))

    def clean_location(self):
        return self.data.get('location', '').strip()

    @commit_on_success
    def save(self):
        user = self.data['user']

        user.location = self.cleaned_data['location'] or None
        user.birthday = self.cleaned_data['birthday'] or None
        if self.cleaned_data['sex'] == '1':
            user.is_male = None
        elif self.cleaned_data['sex'] == '2':
            user.is_male = True
        else:
            user.is_male = False

        user.save()


class FindFriendForm(PrklSuperForm):
    attrs = {
        'size': 10,
    }

    find_friend = forms.CharField(label='Etsi', required=False, widget=forms.widgets.TextInput(attrs=attrs))


class EditDescriptionForm(PrklSuperForm):
    attrs = {
        'rows': 5,
        'cols': 40,
    }

    description = forms.CharField(label='Kuvauksesi', required=False, widget=forms.widgets.Textarea(attrs=attrs))

    def clean_description(self):
        return self.data.get('description', '').strip() or None

    def save(self):
        user = self.data['user']
        user.description = self.cleaned_data['description']

        user.save()

# EOF

