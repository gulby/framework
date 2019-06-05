#!/usr/bin/env bash

# Prepare
if [ -e initialized ]
then
    echo "already initialized"
else
    touch initialized
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    python docker_init.py
fi

# Start
supervisord -n
