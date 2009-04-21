# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.template import Library

register = Library()

@register.filter
def getitem(ob, key):
    return ob.get(key, None)
        

@register.simple_tag
def check_active(req_path, path):
    # Deal with / being a path and all starting with /
    if path == '/' or not path:
        return 'active' if req_path == '/' else 'inactive'
    else:
        return 'active' if req_path.startswith(path) else 'inactive'

@register.filter
def prkltagjoin(tags, joiner):
    return joiner.join([t['name'] for t in tags])

# EOF

