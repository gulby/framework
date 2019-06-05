from server.settings import *


DEPLOYMENT_LEVEL = "unittest"
DEBUG = False
IS_UNIT_TEST = True
IS_FULL_TEST = True if os.environ.setdefault("IS_FULL_TEST", "False") == "True" else False
IS_CHECK_PERFORMANCE_PROBLEM = True
REQUESTS_IS_RECORD_RESULT = True
REQUESTS_USE_CACHE = True
REQUESTS_CACHE_FIRST = True
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

TEMPLATES[0]["OPTIONS"]["string_if_invalid"] = "This_is_not_INVALID"
OUTERMOST_TRANSACTION_NAME_FOR_TEST = "UnitTestTransaction"

# disable CSRF
MIDDLEWARE.remove("django.middleware.csrf.CsrfViewMiddleware")

if "TRAVIS" in os.environ:
    for db in DATABASES.values():
        db.update({"NAME": "unittest_{db_name}".format(db_name=db["NAME"]), "USER": "postgres"})
    OUTERMOST_TRANSACTION_NAME_FOR_TEST = "Transaction"
    IS_FULL_TEST = True


from server.settings_tail import *
