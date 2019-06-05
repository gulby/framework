#!/usr/bin/env bash

server/security/docker_login.sh

docker push deephigh/server_db:latest
docker push deephigh/server_cache:latest
docker push deephigh/server_web:latest
