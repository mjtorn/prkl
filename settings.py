# vim: tabstop=4 expandtab autoindent shiftwidth=4 fileencoding=utf-8
# Django settings for prkl project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG

KLUDGE_STATIC = False

DEBUG_TOOLBAR = False

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ('Markus Törnqvist', 'mjt@fadconsulting.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2' # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'prkl'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
if KLUDGE_STATIC:
    MEDIA_ROOT = '/home/mjt/src/git_checkouts/prkl/media/'
else:
    MEDIA_ROOT = '/var/www/prkl/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@s8x5)1r$2f^qd82ke=5&n2yk#vaq%!&mo2m(4t0)so5oui29('

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.request',
    'web.ctx_proc.strip_path',
    'web.ctx_proc.settings',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    'prkl.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.csrf.middleware.CsrfMiddleware',
    'prkl.middleware.CsrfMiddleware',
    'prkl.middleware.TrueIdMiddleware',
)

if DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
    MIDDLEWARE_CLASSES.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    MIDDLEWARE_CLASSES = tuple(MIDDLEWARE_CLASSES)

ROOT_URLCONF = 'prkl.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'prkl.web',
    'fad_tools.messager',
    'ajax_validation',
    'mediator',
    'qs.queue',
)

if DEBUG_TOOLBAR:
    INSTALLED_APPS = list(INSTALLED_APPS)
    INSTALLED_APPS.append('debug_toolbar')
    INSTALLED_APPS = tuple(INSTALLED_APPS)

if DEBUG_TOOLBAR:
    INTERNAL_IPS = ('127.0.0.1', '88.112.189.238')

AUTHENTICATION_BACKENDS = (
    'prkl.web.auth.PrklRegistrationBackend',
    'prkl.web.auth.PrklModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# Make sure slashes are ok
APPEND_SLASH = True

DEFAULT_FROM_EMAIL = 'yllapito@prkl.es'

# http://www.djangosnippets.org/snippets/342/
TEMPLATE_TAGS = (
    'fad_tools.pagination.templatetags.pagination',
)

# fad_tools.pagination
PAGE_PATH = '/p/'

# Proper testing
TEST_RUNNER = 'noserun.run_tests'

# For GA etc
PRODUCTION = False

try:
    from custom_settings import *
except ImportError:
    pass

# EOF

