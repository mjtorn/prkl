# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.contrib.csrf.middleware import _make_token

from django.core.urlresolvers import reverse

from django.conf import settings

from django.utils.html import escape
from django.utils.safestring import SafeUnicode

from django.template import Library

from dateutil import parser, tz

register = Library()

@register.simple_tag
def do_csrf(request):
    return _make_token(request.COOKIES[settings.SESSION_COOKIE_NAME])

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

@register.filter
def prkltaglinks(tags, request):
    bare_href = '<a href="http://%s%s" class="prkl_tag">%s</a>' % (request.META['HTTP_HOST'], '%s', '%s')

    tag_links = []
    for t in tags:
        rev_tag = reverse('tag', args=(t['name'].lower(),))
        link = bare_href % (rev_tag, escape(t['name']))
        tag_links.append(link)

    out_links = ', '.join(tag_links)

    # Somehow setting prkltaglinks.is_safe = True does not help
#    out = '<span>%s</span>' % out_links
    out = SafeUnicode('<span>%s</span>' % out_links)

    return out
#prkltaglinks.is_safe = True

@register.filter
def as_tz(date, tz_name):
    ## Argh
    # Enforce UTC because the date apparently doesn't know it's utc...
    new_date = parser.parse(date.strftime("%Y-%m-%d %H:%M:%S UTC"))
    dest_tz = tz.gettz(tz_name)
    return new_date.astimezone(dest_tz).strftime("%Y-%m-%d %H:%M:%S")

# EOF

