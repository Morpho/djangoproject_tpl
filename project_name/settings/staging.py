from . import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{{ project_name }}',
        'USER': '{{ project_name }}',
        'PASSWORD': '{{ project_name }}',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
          'init_command': 'SET storage_engine=INNODB', # mysql DB always as INNODB
        }
    },
    'mysql1': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{{ project_name }}',
        'USER': '{{ project_name }}',
        'PASSWORD': '{{ project_name }}',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
          'init_command': 'SET storage_engine=INNODB', # mysql DB always as INNODB
        }
    },
    'mysql2': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': '{{ project_name }}',
        'USER': '{{ project_name }}',
        'PASSWORD': '{{ project_name }}',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {
          'init_command': 'SET storage_engine=INNODB', # mysql DB always as INNODB
        }
    }
}