# -*- coding: utf-8 -*-
import os.path
import sys
import re
import djcelery
djcelery.setup_loader()

PROJECT_SLUG = '{{ project_name }}'
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Matthias', 'matthias@scholz.ms'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': PROJECT_SLUG,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
          'init_command': 'SET storage_engine=INNODB', # mysql DB always as INNODB
        }
    },
    'mysql1': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': PROJECT_SLUG,
        'USER': '',
        'PASSWORD': '',
        'HOST': 'mysql1...',
        'PORT': '',
        'OPTIONS': {
          'init_command': 'SET storage_engine=INNODB', # mysql DB always as INNODB
        }
    },
    'mysql2': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': PROJECT_SLUG,
        'USER': '',
        'PASSWORD': '',
        'HOST': 'mysql2...',
        'PORT': '',
        'OPTIONS': {
          'init_command': 'SET storage_engine=INNODB', # mysql DB always as INNODB
        }
    },
    'jobs': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'jobs',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
          'init_command': 'SET storage_engine=INNODB', # mysql DB always as INNODB
        }
    },
}

# DATABASE_ROUTERS = ['ROUTERAPP.routers.MasterMasterRouter',]

REDIS_PORT = "0"

BROKER_URL = "redis://localhost:6379/%s" % REDIS_PORT
CELERY_IMPORTS = ("APPNAME.tasks", )
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_SEND_EVENTS = True
CELERY_IGNORE_RESULT = False
CELERY_TRACK_STARTED = True
CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
BROKER_POOL_LIMIT = None
CELERY_DISABLE_RATE_LIMITS = True

ALLOWED_HOSTS = ['PROJECT_HOST',]

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': '127.0.0.1:6379:%s' % REDIS_PORT,
        'OPTIONS': {
            'CLIENT_CLASS': 'redis_cache.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'de-de'
SITE_ID = 1
USE_I18N = True
USE_L10N = True
USE_TZ = True
ugettext = lambda s: s

LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, 'locale'),
)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'layout', 'media')
MEDIA_URL = '/media/'
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'site-static')

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "site-static"),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

SECRET_KEY = '{{ secret_key }}'

TEMPLATE_CONTEXT_PROCESSORS = (
	#'django.core.context_processors.debug',
	#'django.core.context_processors.i18n',
	#'django.core.context_processors.media',
	'django.core.context_processors.request',
	'django.contrib.auth.context_processors.auth',
	'django.contrib.messages.context_processors.messages',
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = os.path.join(PROJECT_ROOT, 'urls')
WSGI_APPLICATION = os.path.join(PROJECT_ROOT, 'wsgi', 'application')

TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, 'layout', 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'gunicorn',
    'djcelery'
    'django_extensions',
    'constance',
    'debug_toolbar',
)

CONSTANCE_CONFIG = {
    'SETTING_DEF': (True, u'Description'),
}

def custom_show_toolbar(request):
    return True if request.user.is_staff else False

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
    'SHOW_TOOLBAR_CALLBACK': custom_show_toolbar,
    'HIDE_DJANGO_SQL': False,
    'ENABLE_STACKTRACES' : True,
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': os.path.join(PROJECT_ROOT, 'logs', 'djangodebug.log'),
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': False,
        },
        PROJECT_SLUG: {
            'handlers': ['logfile'],
            'level': 'DEBUG', # Or maybe INFO
            'propagate': False
        },
    }
}
