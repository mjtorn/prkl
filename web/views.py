# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.http import HttpResponse

# Create your views here.

def index(request):
    """Our index page
    """

    return HttpResponse('lol', content_type='text/plain')

# EOF

