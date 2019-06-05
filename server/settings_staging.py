from server.settings import *


DEPLOYMENT_LEVEL = "staging"

# staging DB
for db in DATABASES.values():
    db.update({"HOST": "192.168.1.13", "NAME": "server_staging_db"})


# tablespace
#
# [bash]
# mkdir /mnt/4TB/postgres
# mkdir /mnt/4TB/postgres/server_staging_db
# sudo chown -R postgres.postgres /mnt/4TB/postgres/
#
# [psql]
# create tablespace tbs_server_staging_db owner server_user location '/mnt/4TB/postgres/server_staging_db';
# CREATE DATABASE server_staging_db;
# GRANT ALL PRIVILEGES ON DATABASE server_staging_db TO server_user;
#
# [conf]
# sudo vi /etc/postgresql/10/main/pg_hba.conf
# sudo vi /etc/postgresql/10/main/postgresql.conf
# sudo service postgresql stop
# sudo service postgresql start
#
# [migrate]
# export DEPLOYMENT_LEVEL=staging
# python manage.py migrate
#
# django
DEFAULT_TABLESPACE = "tbs_server_staging_db"
DEFAULT_INDEX_TABLESPACE = "tbs_server_staging_db"

MEDIA_ROOT = os.path.join("/mnt/48TB", "media")

from server.settings_tail import *
