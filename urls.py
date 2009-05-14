from django.conf.urls.defaults import *

def handler500(request):
    import sys
    import traceback
    from django.views.defaults import server_error
    exc_type, exc_value, exc_tb = sys.exc_info()
    subj = '%s: %s' % (exc_type, exc_value)
    formatted_tb = traceback.format_exc(exc_tb)

    send_mail(subj, formatted_tb, 'yllapito@prkl.es', ('mjt@prkl.es',))

    return server_error(request)

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^prkl/', include('prkl.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
    (r'^', include('web.urls')),
)
