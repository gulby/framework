#!/usr/bin/env bash

if [[ $OSTYPE == "darwin"* ]];
then
    psql -d postgres -a -f myscript/drop_db.sql
else
    sudo -u postgres psql -a -f myscript/drop_db.sql
fi

myscript/create_db.sh

myscript/migrate.sh
python docker_init.py
