# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf import settings as django_settings

def strip_path(request):
    return {
        'strip_path': request.META['PATH_INFO'].strip('/')
    }

def settings(request):
    return {
        'production': django_settings.PRODUCTION,
    }

# EOF

