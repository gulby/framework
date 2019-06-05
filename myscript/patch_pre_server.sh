#!/usr/bin/env bash

# prepare patch
if [ ! -e myscript/patch/wkhtmltopdf/ ]
then
    mkdir myscript/patch/wkhtmltopdf
    cd myscript/patch/wkhtmltopdf
    wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.3/wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
    tar vxf wkhtmltox-0.12.3_linux-generic-amd64.tar.xz
    cp wkhtmltox/bin/wk* .
    cd ../../..
fi

docker build -t deephigh/server_web -f Dockerfile_web .
docker network create server_network 2> /dev/null
docker rm -f server_web_production
docker run  --name server_web_production -itd -p 80:80 -e DEPLOYMENT_LEVEL=production --network server_network --restart unless-stopped -v ~/server_local/media:/home/service/media -v ~/server_local/data:/home/service/data deephigh/server_web
docker rmi -f $(docker images | grep "<none>" | awk "{print \$3}")
