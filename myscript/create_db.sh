#!/usr/bin/env bash

if [[ $OSTYPE == "darwin"* ]];
then
    PSQL_COMMAND="psql -d postgres"
else
    PSQL_COMMAND="sudo -u postgres psql"
fi

PASSWORD=$(<server/security/PASSWORD)

while read line; do
    replaced=$(echo $line | sed -e "s/__PASSWORD__/'$PASSWORD'/g")
    echo $replaced | $PSQL_COMMAND
done < myscript/create_db.sql
