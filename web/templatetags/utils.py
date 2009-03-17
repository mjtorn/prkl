# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.template import Library

register = Library()

@register.simple_tag
def check_active(req_path, path):
    # Deal with / being a path and all starting with /
    if path == '/':
        return 'active' if req_path == '/' else 'inactive'
    else:
        return 'active' if req_path.startswith(path) else 'inactive'

# EOF

