#!/usr/bin/env bash

if [[ $OSTYPE == "darwin"* ]];
then
    psql -d server_db -a -f myscript/truncate_table.sql
else
    sudo -u postgres psql -d server_db -a -f myscript/truncate_table.sql
fi
