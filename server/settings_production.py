from server.settings import *

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(dsn="https://cf1b1c996d8d48ba9e734e58755bcb7c@sentry.io/1393418", integrations=[DjangoIntegration()])


DEBUG = False
DEPLOYMENT_LEVEL = "production"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

# production DB
for db in DATABASES.values():
    db.update({"HOST": ""})

# Root URL
ROOT_URL = "http://www.deephigh.net"


from server.settings_tail import *
