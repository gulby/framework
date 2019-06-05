#!/usr/bin/env bash

# prerequisite 설치 : 장비당 한번만 실행하면 됨
# myscript/deploy_prerequisite.sh

# 파이썬 가상 환경 설정 : 현재까지 파악한 바로는 가상환경 activate 는 shell script 내에서 한방에는 안되고 터미널에서 별도 실행해야 함
conda create --name server_env python=3.6
echo "conda activate server_env" >> .env
cd ..
cd server/

# 모듈 설치
myscript/deploy_packages.sh

# DB 구성
if [[ "$OSTYPE" == "darwin"* ]];
then
    psql -d postgres -a -f myscript/create_db.sql
else
    sudo -u postgres psql -a -f myscript/create_db.sql
fi

# settings_machine 설치
cp server/settings_machine_template.py server/settings_machine.py

# server migrate
myscript/migrate.sh

# init db
python docker_init.py
