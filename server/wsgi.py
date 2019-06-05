"""
WSGI config for server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

DEPLOYMENT_LEVEL = os.environ.setdefault("DEPLOYMENT_LEVEL", "development")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings_{dlevel}".format(dlevel=DEPLOYMENT_LEVEL))

application = get_wsgi_application()
