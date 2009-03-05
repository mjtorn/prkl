# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db.transaction import commit_on_success

from django import forms

from web import models

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
