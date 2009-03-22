# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf.urls.defaults import *

from django.conf import settings

import views
import api_views

handler404 = 'prkl.web.views.notfound'

urlpatterns = patterns('',
    url(r'^forgot_password/$', views.forgot_password, name='forgot_password'),
    url(r'^reset_password/((?:[a-z0-9])+-(?:[a-z0-9])+)/$', views.reset_password, name='reset_password'),
    url(r'^logout', views.logout_view, name='logout'),
    url(r'^top/$', views.top, name='top'),
    url(r'^bottom/$', views.bottom, name='bottom'),
    url(r'^vote/(\d+)/(up|down)/([a-z/]+)?/$', views.vote, name='vote'),
    url(r'^faq/$', views.notfound, name='faq'),
    url(r'^members/$', views.notfound, name='members'),
    url(r'^api/extend_vip/(?P<username>[a-zA-Z0-9_]+)/(?P<period>30|180|360)/', api_views.extend_vip, name='api_extend_vip')
)

if settings.KLUDGE_STATIC:
    urlpatterns += patterns('',
    # Static
    (r'^media/(?P<path>.*)/?$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

urlpatterns += patterns('',
    url(r'^$', views.index, name='index'),
)

# EOF

