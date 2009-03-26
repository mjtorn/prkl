# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate
from django.contrib.auth import models as auth_models
from django.contrib.auth import tokens

from django.db.transaction import commit_on_success

from django import forms

from web import models

import datetime

class RequestResetForm(forms.Form):
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


class PasswordResetForm(forms.Form):
    error_messages = {
        'required': 'Annathan uuden salasanasi :)'
    }
    new_password = forms.CharField(label='Uusi salasana', error_messages=error_messages, widget=forms.widgets.PasswordInput())


class LoginForm(forms.Form):
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


class RegisterForm(forms.Form):
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
        user = models.User.objects.create_user(username, email, password)

        # Also see if this was an invite
        try:
            invite = models.FriendInvite.objects.get(recipient=email)
            invite.registered_at = datetime.datetime.now()
            user_invite_count = models.FriendInvite.objects.filter(sent_by_user=invite.sent_by_user, registered_at__isnull=False).count()
            if user_invite_count < 5:
                if invite.sent_by_user.is_vip:
                    invite.sent_by_user.extend_vip(datetime.timedelta(days=5))
                else:
                    invite.sent_by_user.set_vip(datetime.datetime.now() + datetime.timedelta(days=5))
            invite.save()
        except models.FriendInvite:
            pass
        return user


class SubmitPrklForm(forms.Form):
    error_messages = {
        'required': 'Taisi jäädä prkl kirjoittamatta!',
    }
    attrs = {
        'cols': 80,
        'rows': 3,
    }
    content = forms.CharField(label='Sinun prkleesi', error_messages=error_messages, widget=forms.widgets.Textarea(attrs=attrs))

    def clean_content(self):
        content = self.data['content'].strip()

        if not content.lower().startswith('tänään'):
            raise forms.ValidationError('Aloitathan Prkleesi sanalla tänään')

        # FIXME: Allow some amount of . and ! and maybe ? at the end
        if not content.lower().endswith('prkl'):
            raise forms.ValidationError('Päätäthän Prkleesi sanalla prkl')

        return content

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


class CommentPrklForm(forms.Form):
    error_messages = {
        'required': 'Kirjoitathan kommentin!',
    }

    attrs = {
        'rows': 5,
        'cols': 80,
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


class InviteFriendForm(forms.Form):
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

class ChangePicForm(forms.Form):
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

# EOF

