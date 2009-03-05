# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.shortcuts import render_to_response

from django.template import RequestContext

# Create your views here.

def index(request):
    """Our index page
    """

    context = {
        'title': 'Etusivu'
    }
    req_ctx = RequestContext(request, context)

    return render_to_response('index.html', req_ctx)

# EOF

