# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

def strip_path(request):
    return {
        'strip_path': request.META['PATH_INFO'].strip('/')
    }

# EOF

