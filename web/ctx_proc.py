# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

import forms

def check_login(request):
    if not request.user.id:
            login_form = forms.LoginForm(request.POST.copy() or None)
    else:
        login_form = None

    return {
        'login_form': login_form
    }

# EOF

