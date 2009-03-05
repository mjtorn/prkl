# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8

from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    (r'^top', views.top),
    (r'^bottom', views.bottom),
    (r'^', views.index),
)

# EOF

