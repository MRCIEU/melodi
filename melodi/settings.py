"""
Django settings for melodi project.

Generated by 'django-admin startproject' using Django 1.8.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from datetime import timedelta
from celery.schedules import crontab,timedelta
from django.core.urlresolvers import reverse_lazy
import config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config.secret_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

#ALLOWED_HOSTS = []

#Add this for public
ALLOWED_HOSTS = ['melodi.biocompute.org.uk','www.melodi.biocompute.org.uk','melodi.mrcieu.ac.uk']

# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'browser',
    'social_auth',
    'django.contrib.humanize'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    #'django.middleware.cache.UpdateCacheMiddleware', #need this for cache
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware', #need this for cache
)

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.google.GoogleOAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_ENABLED_BACKENDS = ('google')
LOGIN_URL = '/login/'
LOGIN_ERROR_URL = '/login-error/'
LOGIN_REDIRECT_URL = reverse_lazy('home')

GOOGLE_OAUTH2_CLIENT_ID = '744265706742-h9l3etr7pdboc8d0h0b14biiemtfsbvb.apps.googleusercontent.com'
GOOGLE_OAUTH2_CLIENT_SECRET = 'BsQyz4BxaC82kYD_O5UHcgaF'
#GOOGLE_WHITE_LISTED_DOMAINS = ['bristol.ac.uk']
SOCIAL_AUTH_USER_MODEL = 'auth.User'


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'social_auth.context_processors.social_auth_by_type_backends'
)

ROOT_URLCONF = 'melodi.urls'

APPEND_SLASH = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'browser/templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'melodi.wsgi.application'

SESSION_SERIALIZER='django.contrib.sessions.serializers.PickleSerializer'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    #'default': {
    #    'ENGINE': 'django.db.backends.sqlite3',
    #    'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #}
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'read_default_file': '/var/django/melodi/mysql.cnf',
        },
    }
}

# NEO4J_DATABASES = {
#     'default' : {
#         'HOST':'10.0.2.2',
#         'PORT':7474,
#         'ENDPOINT':'/db/data'
#     }
# }

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
#STATIC_ROOT = '/var/django/melodi/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "static/")
STATIC_URL = '/static/'

MEDIA_ROOT = '/var/django/melodi/'
DATA_FOLDER = os.path.join(BASE_DIR,"data/")

# CELERY SETTINGS
BROKER_URL = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACKS_LATE = True
#restart the worker process after every task to avoid memory leaks
CELERYD_MAX_TASKS_PER_CHILD = 1

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            #'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'debug.log'),
            #'filename': '/tmp/debug.log',
            'formatter': 'verbose'
        },
	'console': {
	    'level': 'WARNING',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        #'django': {
        #    'handlers':['file'],
        #    'propagate': True,
        #    'level':'INFO',
        #},

	'celery': {
            'handlers': ['console'],
            'propagate': False,
            'level': 'WARNING',
        },

        'browser': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    }
}

#CACHE_MIDDLEWARE_ALIAS = 'default'
#CACHE_MIDDLEWARE_SECONDS = 60480000
#CACHE_MIDDLEWARE_KEY_PREFIX = ''

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            #"SOCKET_TIMEOUT": 50,
        },
        "KEY_PREFIX": "melodi",
        'TIMEOUT': None
    }
}


#CACHES = {
#    'default': {
#        #'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
#        'LOCATION': 'melodi_cache',
#        'TIMEOUT': None
#    }
#}

CELERYBEAT_SCHEDULE = {
    #'t1': {
    #    'task': 'tasks.test_scheduler',
    #    'schedule': timedelta(seconds=10),
    #},
	#update pubmed-mesh relationships every dat at 3am
    'dm': {
        'task': 'tasks.daily_mesh',
        #'schedule': timedelta(hours=1),
		'schedule': crontab(hour=3, minute=0),#
    },
    #'neo': {
    #    'task': 'tasks.neo4j_check',
    #    #'schedule': timedelta(hours=1),
	#	'schedule': timedelta(minutes=30),#
    #},

}
#  Logging
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'filters': {
#         'require_debug_false': {
#             '()': 'django.utils.log.RequireDebugFalse'
#          }
#     },
#     'formatters': {
#         'verbose': {
#             'format': '[%(asctime)s] %(levelname)-8s %(process)d %(thread)d %(name)s:%(message)s',
#             'datefmt': '%Y-%m-%d %a %H:%M:%S'
#         },
#     },
#     'handlers': {
#         'null': {
#             'level': 'DEBUG',
#             'class': 'django.utils.log.NullHandler',
#         },
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose'
#         },
#         'local_file': {
#             'level': 'DEBUG',
#             'class': 'logging.handlers.RotatingFileHandler',
#             'formatter': 'verbose',
#             #'filename': '%s/debug.log' % APP_ROOT,
#             'filename': os.path.join(BASE_DIR, 'debug2.log'),
#             'maxBytes': 1024 * 1024 * 10,
#         },
#         'syslog': {
#             'level': 'INFO',
#             'class': 'logging.handlers.SysLogHandler',
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'filters': ['require_debug_false'],
#             'class': 'django.utils.log.AdminEmailHandler',
#             'include_html': True,
#         }
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['null'],
#             'propagate': True,
#             'level': 'INFO',
#         },
#         'django.request': {
#             'handlers': ['mail_admins', 'console', 'local_file'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#     },
#     'root': {
#              'handlers': ['console', 'local_file'],
#              'level': 'DEBUG',
#     }
# }
