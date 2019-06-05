#!/usr/bin/env bash

docker rm -f $(docker ps -a | grep "server_cache" | awk "{print \$1}")
docker pull redis:latest
docker build -t deephigh/server_cache -f Dockerfile_cache .
docker network create server_network 2> /dev/null
docker run --name server_cache -itd -p 16379:6379 --network server_network --restart unless-stopped deephigh/server_cache
docker rmi -f $(docker images | grep "<none>" | awk "{print \$3}")
