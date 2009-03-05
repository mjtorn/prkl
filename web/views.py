# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.http import HttpResponseRedirect

from django.shortcuts import render_to_response

from django.template import RequestContext

from web import forms

# Create your views here.

def index(request):
    """Our index page
    """

    data = request.POST.copy() or None
    if data:
        data['user'] = request.user

    submit_prkl_form = forms.SubmitPrklForm(data)

    if submit_prkl_form.is_bound:
        if submit_prkl_form.is_valid():
            submit_prkl_form.save()
            
            return HttpResponseRedirect(request.META['PATH_INFO'])

    context = {
        'title': 'Etusivu',
        'form': submit_prkl_form
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)

# EOF

