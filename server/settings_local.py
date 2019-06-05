from server.settings import *


DEPLOYMENT_LEVEL = "local"

# local DB
for db in DATABASES.values():
    db.update({"HOST": "server_db"})

# local cache
CACHES["default"]["LOCATION"] = "redis://server_cache:6379/0"
CACHES["email_onetime_password"]["LOCATION"] = "redis://server_cache:6379/1"

# Root URL
ROOT_URL = "http://localhost:8080"


from server.settings_tail import *
