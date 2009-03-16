# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.auth import authenticate
from django.contrib.auth import models as auth_models

from django.db.transaction import commit_on_success

from django import forms

from web import models

class LoginForm(forms.Form):
    error_messages = {
        'required': 'Tämä kenttä tarvitaan',
    }
    username = forms.CharField(label='Tunnus', error_messages=error_messages)
    password = forms.CharField(label='Salasana', error_messages=error_messages, widget=forms.widgets.PasswordInput())

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
    reg_username = forms.CharField(label='Tunnus', error_messages=error_messages)
    reg_password = forms.CharField(label='Salasana', widget=forms.widgets.PasswordInput(), error_messages=error_messages)
    reg_email = forms.EmailField(label='Sähköposti', error_messages=error_messages)

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
    content = forms.CharField(label='Sinun prkleesi', widget=forms.widgets.TextInput())

    def clean_content(self):
        content = self.data['content']
        print content

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
        if self.data['user'].id:
            new_prkl.user = self.data['user']
        new_prkl.save()

# EOF

