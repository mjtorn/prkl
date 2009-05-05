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
        'required': 'Jotain tarvitaan, valitse edes Satunnainen ;)',
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

        if len(content) > 1024:
            raise forms.ValidationError('Tänään prkleesi on yli 1024 merkkiä prkl')

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
        'required': 'Annathan kaverisi sähköpostin',
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

    error_messages = {
        'required': 'Ketä mahdat etsiä?',
    }

    find_friend = forms.CharField(label='Etsi', required=True, error_messages=error_messages, widget=forms.widgets.TextInput(attrs=attrs))


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


class MsgToUserForm(PrklSuperForm):
    subject_attrs = {
        'size': 15,
    }
    subject_errors = {
        'required': 'Otsikko tarvitaan, edes "moi" :)',
    }

    body_attrs = {
        'rows': 5,
        'cols': 60,
    }
    body_errors = {
        'required': 'Jotain sisältöä tarvitaan :)',
    }

    subject = forms.CharField(label='Otsikko', error_messages=subject_errors, widget=forms.widgets.TextInput(attrs=subject_attrs))
    body = forms.CharField(label='Viestisi', error_messages=body_errors, widget=forms.widgets.Textarea(attrs=body_attrs))

    @commit_on_success
    def save(self):
        message = models.PrivMessage()
        message.subject = self.cleaned_data['subject']
        message.body = self.cleaned_data['body']
        message.sender = self.data['sender']
        message.recipient = self.data['recipient']

        message.save()


class UserSearchForm(PrklSuperForm):
    sex_choices = ((1, 'Ei kerro'), (2, 'Mies'), (3, 'Nainen'), (4, 'Ei väliä'))
    sex_errors = {
        'required': 'Valitse edes "Ei kerro"',
        'invalid_choice': 'Tuo ei ole sukupuoli',
    }

    attrs = {
        'size': 12,
    }

    age_attrs = {
        'size': 3,
    }
    age_errors = {
        'invalid': 'Tämä ei näytä numerolta',
    }

    username = forms.CharField(label='Käyttäjä', required=False, widget=forms.widgets.TextInput(attrs=attrs))
    location = forms.CharField(label='Sijainti', required=False, widget=forms.widgets.TextInput(attrs=attrs))
    sex = forms.ChoiceField(label='Sukupuoli', error_messages=sex_errors, choices=sex_choices)
    age_low = forms.IntegerField(label='Ikä alkaen', required=False, error_messages=age_errors, widget=forms.widgets.TextInput(attrs=age_attrs))
    age_high = forms.IntegerField(label='Ikä päättyen', required=False, error_messages=age_errors, widget=forms.widgets.TextInput(attrs=age_attrs))

    def search(self):
        """Breaking the law! Breaking the law!
        """

        now = datetime.datetime.now()

        # Shortcut
        d = self.cleaned_data

        users = models.User.objects.filter()
        if d['username']:
            users = users.search(d['username'])

        if d['location']:
            users = users.search_location(d['location'])

        if d['sex']:
            sex = int(d['sex'])
            if sex == 1:
                users = users.filter(is_male__isnull=True)
            elif sex == 2:
                users = users.filter(is_male=True)
            elif sex == 3:
                users = users.filter(is_male=False)

        if d['age_low']:
            age_low = int(d['age_low'])
            age_low_bday = now - datetime.timedelta(days=365 * age_low)
            users = users.filter(birthday__lte=age_low_bday)

        if d['age_high']:
            age_high = int(d['age_high'])
            age_high_bday = now - datetime.timedelta(days=365 * age_high)
            users = users.filter(birthday__gte=age_high_bday)

        return users

    def as_custom(self):
        """This crap is based on forms.Form's _html_output
        """

        # These would have been passed
        # but alter slightly
        normal_row = '<tr>%s'
        normal_content= '<td>%(label)s<br />%(field)s <br /><span class="error">%(errors)s</span> %(help_text)s '
        age_content= '<td>%(label)s<br />%(age_low)s-%(age_high)s <br /><span class="error">%(errors)s</span> %(help_text)s '
        error_row = '%s'
        row_ender = '%s</tr>'

        # Cheat key order to match table
        keys = ('username', 'age_low', 'age_high', 'location', 'sex')

        # Check modulo to see if we break a line
        i = 0
        output = []
        for name in keys:
            field = self.fields[name]
            bf = forms.forms.BoundField(self, field, name)
            ## Directly use PrklErrorField
            bf_errors = PrklErrorField([conditional_escape(error) for error in bf.errors])
            ## Skip hidden fields, don't have any
            # Don't care about separate-row variable
            if bf_errors:
                output.append(error_row % force_unicode(bf_errors))

            # Age is special
            if bf.label and name != 'age_low' and name != 'age_high':
                label = conditional_escape(force_unicode('%s:' % bf.label))
                label = bf.label_tag(label) or ''
            elif bf.label and name == 'age_low':
                label = 'Ikä:'
                age_content = age_content % {
                    'label': force_unicode(label),
                    'age_low': unicode(bf),
                    'age_high': '%(age_high)s',
                    'errors': force_unicode(bf_errors),
                    'help_text': '',
                }
            elif bf.label and name == 'age_high':
                label = ''
                age_content = age_content % {
                    'age_high': unicode(bf),
                    'errors': force_unicode(bf_errors),
                    'help_text': '',
                }
                i -= 1
            else:
                label = ''

            # Retain as is
            if field.help_text:
                help_text = help_text_html % force_unicode(field.help_text)
            else:
                help_text = u''

            # Content
            if name == 'age_low':
                pass
            elif name == 'age_high':
                content = age_content
                output.append(row_ender % content)
            else:
                content = normal_content % {'errors': force_unicode(bf_errors), 'label': force_unicode(label), 'field': unicode(bf), 'help_text': help_text}

                # Do we break the line?
                if i % 2 == 0:
                    output.append(normal_row % content)
                else:
                    output.append(row_ender % content)

            i += 1
        return mark_safe(u'\n'.join(output))


class ReplyForm(PrklSuperForm):
    body_attrs = {
        'rows': 5,
        'cols': 60,
    }
    body_errors = {
        'required': 'Jotain sisältöä tarvitaan :)',
    }

    in_reply_to = forms.IntegerField(widget=forms.widgets.HiddenInput())
    body = forms.CharField(label='Viestisi', error_messages=body_errors, widget=forms.widgets.Textarea(attrs=body_attrs))
    prefix = in_reply_to

    def clean_in_reply_to(self):
        in_reply_to = self.data['in_reply_to']
        if self.data.has_key('user'):
            user = self.data['user']

            try:
                # Remember parent
                self.parent = models.PrivMessage.objects.get(id=in_reply_to, recipient=user)
            except models.PrivMessage.DoesNotExist:
                raise forms.ValidationError('Viestiä ei löydy tai se ei kuulu sinulle')

        return in_reply_to

    @commit_on_success
    def save(self):
        message = models.PrivMessage()
        message.body = self.cleaned_data['body']
        # All this is smuggled
        message.sender = self.data['user']
        message.subject = self.parent.subject
        message.recipient = self.parent.sender
        message.parent = self.parent

        message.save()

        return message

# EOF

