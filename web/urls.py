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
    url(r'^top//p/(?P<page>\d+)/(?P<records>\d+)', views.top, name='top'),
    url(r'^top/$', views.top, name='top'),
    url(r'^bottom//p/(?P<page>\d+)/(?P<records>\d+)', views.bottom, name='bottom'),
    url(r'^bottom/$', views.bottom, name='bottom'),
    url(r'^vote/(\d+)/(up|down)/([a-zA-Z0-9/]+)?/$', views.vote, name='vote'),
    url(r'^like/(\d+)/(yes|no)/([a-zA-Z0-9/]+)?/$', views.like, name='like'),
    url(r'^prkl/(\d+)/$', views.prkl, name='prkl'),
    url(r'^faq/$', views.notfound, name='faq'),
    url(r'^about_vip/$', views.about_vip, name='about_vip'),
    url(r'^edit_profile/$', views.edit_profile, name='edit_profile'),
    url(r'^member/([a-zA-Z0-9-]+)/$', views.member, name='member'),
    url(r'^members//p/(?P<page>\d+)/(?P<records>\d+)', views.members, name='members'),
    url(r'^members/$', views.members, name='members'),
    url(r'^set_form_visibility/', views.set_form_visibility, name='set_form_visibility'),
    url(r'^api/extend_vip/(?P<username>[a-zA-Z0-9_]+)/(?P<period>30|180|360)/', api_views.extend_vip, name='api_extend_vip'),
    url(r'^api/post_prkl/', api_views.post_prkl, name='api_post_prkl'),
)

if settings.KLUDGE_STATIC:
    urlpatterns += patterns('',
    # Static
    (r'^media/(?P<path>.*)/?$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
)

urlpatterns += patterns('',
    url(r'^p/(?P<page>\d+)/(?P<records>\d+)', views.index, name='index'),
    url(r'^$', views.index, name='index'),
)

# EOF

