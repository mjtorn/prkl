# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf.urls.defaults import *

from django.conf import settings

import forms
import views
import api_views

handler404 = 'prkl.web.views.notfound'

urlpatterns = patterns('',
    url(r'^forgot_password/$', views.forgot_password, name='forgot_password'),
    url(r'^reset_password/((?:[a-z0-9])+-(?:[a-z0-9])+)/$', views.reset_password, name='reset_password'),
    url(r'^register/((?:[a-z0-9])+-(?:[a-z0-9])+-(?:[a-z0-9])+)/$', views.register, name='register'),
    url(r'^logout', views.logout_view, name='logout'),
    url(r'^top//p/(?P<page>\d+)/(?P<records>\d+)', views.top, name='top'),
    url(r'^top/$', views.top, name='top'),
    url(r'^bottom//p/(?P<page>\d+)/(?P<records>\d+)', views.bottom, name='bottom'),
    url(r'^bottom/$', views.bottom, name='bottom'),
    url(r'^vote/(\d+)/(up|down)/(.+)?/$', views.vote, name='vote'),
    url(r'^like/(\d+)/(yes|no)/(.+)?/$', views.like, name='like'),
    url(r'^prkl/(\d+)/$', views.prkl, name='prkl'),
    url(r'^faq/$', views.faq, name='faq'),
    url(r'^about_vip/$', views.about_vip, name='about_vip'),
    url(r'^edit_profile/$', views.edit_profile, name='edit_profile'),
    url(r'^inbox/$', views.user_inbox, name='user_inbox'),
    url(r'^sent/$', views.user_sent, name='user_sent'),
    url(r'^member/([a-zA-Z0-9-]+)/msg_to/$', views.msg_to_user, name='msg_to_user'),
    url(r'^member/([a-zA-Z0-9-]+)/$', views.member, name='member'),
    url(r'^members//p/(?P<page>\d+)/(?P<records>\d+)', views.members, name='members'),
    url(r'^members/$', views.members, name='members'),
    url(r'^search/$', views.search, name='search'),
    url(r'^search//p/(?P<page>\d+)/(?P<records>\d+)', views.search, name='search'),
    url(r'^set_form_visibility/', views.set_form_visibility, name='set_form_visibility'),
    url(r'^mark_msg_read/', views.mark_msg_read, name='mark_msg_read'),
    url(r'^post_reply/', views.post_reply, name='post_reply'),
    url(r'^incoming/sms/', views.sms_incoming, name='sms_incoming'),
    url(r'^incoming/receipt/', views.receipt_incoming, name='receipt_incoming'),
    url(r'^validate_reply/$', 'ajax_validation.views.validate', {'form_class': forms.ReplyForm}, 'reply_form_validate'),

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
    url(r'^(?P<tag>.+)/p/(?P<page>\d+)/(?P<records>\d+)', views.index, name='index'),
    url(r'^(?P<tag>.+)', views.index, name='index'),
    url(r'^$', views.index, name='index'),
)

# EOF

