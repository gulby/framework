from django.conf import settings
from server.settings_machine import *


if settings.DEBUG:
    # django-debug-toolbar
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": lambda request: True}
    settings.INSTALLED_APPS.append("debug_toolbar")
    settings.MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
else:
    DEBUG_PROPAGATE_EXCEPTIONS = True
