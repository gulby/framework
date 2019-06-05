#!/usr/bin/env bash

py.test --profile $1
snakeviz ./prof/combined.prof
