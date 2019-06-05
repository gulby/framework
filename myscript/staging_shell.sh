#!/usr/bin/env bash

export DEPLOYMENT_LEVEL=staging
python manage.py shell
export DEPLOYMENT_LEVEL=
