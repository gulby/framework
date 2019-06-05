#!/usr/bin/env bash

python manage.py migrate --noinput
py.test base/
myscript/check.sh
