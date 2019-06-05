#!/usr/bin/env bash

docker rm -f $(docker ps -a | grep "server_db" | awk "{print \$1}")
docker pull postgres:latest
docker build -t deephigh/server_db -f Dockerfile_db .
docker network create server_network 2> /dev/null
docker run --name server_db -itd -p 15432:5432 -e POSTGRES_PASSWORD=wlgoakstp1234 --network server_network --restart unless-stopped deephigh/server_db
docker rmi -f $(docker images | grep "<none>" | awk "{print \$3}")

myscript/make_local_web.sh
