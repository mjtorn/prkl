# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf.urls.defaults import *

from django.conf import settings

import views

urlpatterns = patterns('',
    (r'^logout', views.logout_view),
    (r'^top', views.top),
    (r'^bottom', views.bottom),
)

if settings.KLUDGE_STATIC:
    urlpatterns += patterns('',
    # Static
    (r'^media/(?P<path>.*)/?$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

urlpatterns += patterns('',
    (r'^', views.index),
)

# EOF

