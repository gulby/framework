#!/usr/bin/env bash

myscript/format_by_black.sh
myscript/unit_test.sh $1 $2 $3 $4 $5
echo
python manage.py check
echo
echo "flake8 start..."
flake8 .
echo "flake8 end"
