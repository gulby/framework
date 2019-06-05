#!/usr/bin/env bash

if [[ $OSTYPE == "darwin"* ]];
then
    sudo psql postgres -U server_user
else
    sudo -u postgres psql -d server_db
fi
