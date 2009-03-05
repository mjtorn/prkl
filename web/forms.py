# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.db.transaction import commit_on_success

from django import forms

from web import models

class SubmitPrklForm(forms.Form):
    prkl = forms.CharField(label='Sinun prkleesi', widget=forms.widgets.TextInput())

    @commit_on_success
    def save(self):
        new_prkl = models.Prkl()
        new_prkl.content = self.cleaned_data['prkl']
        if self.data['user'].id:
            new_prkl.user = self.data['user']
        new_prkl.save()

# EOF

