# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf.urls.defaults import *

from django.conf import settings

import views

urlpatterns = patterns('',
    url(r'^logout', views.logout_view, name='logout'),
    url(r'^top', views.top, name='top'),
    url(r'^bottom', views.bottom, name='bottom'),
    url(r'^faq', views.index, name='faq'),
    url(r'^members', views.index, name='members'),
)

if settings.KLUDGE_STATIC:
    urlpatterns += patterns('',
    # Static
    (r'^media/(?P<path>.*)/?$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

urlpatterns += patterns('',
    url(r'^', views.index, name='index'),
)

# EOF

