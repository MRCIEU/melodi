"""
WSGI config for melodi project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os,sys,site

sys.path.append('/app/django_project')
sys.path.append('/app/django_project/melodi')

# Add the site-packages of the chosen virtualenv to work with
#site.addsitedir('/var/django/melodi/venv/lib64/python2.7/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = "melodi.settings"

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
