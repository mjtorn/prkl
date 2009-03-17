# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate
from django.contrib.auth import models as auth_models
from django.contrib.auth import tokens

from django.db.transaction import commit_on_success

from django import forms

from web import models

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

        exists = (auth_models.User.objects.filter(username=username).count() > 0)
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
        username = self.cleaned_data['reg_username']
        password = self.cleaned_data['reg_password']
        email = self.cleaned_data['reg_email']
        user = auth_models.User.objects.create_user(username, email, password)
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
            new_prkl.user = user
        new_prkl.save()

# EOF

