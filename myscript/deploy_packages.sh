#!/usr/bin/env bash

# sudo 권한 미리 확보
sudo ls

# conda 설치
# rm conda_install_fail.txt 2> /dev/null
# while read requirement; do conda install --yes $requirement || echo $requirement >> conda_install_fail.txt; done < requirements_conda.txt
pip install -U -r requirements_conda.txt

# pip 설치
pip install -U -r requirements_pip.txt

# python 단 설치
python myscript/deploy_packages.py

# mecab 설치
cd myscript/thirdparty
./install_mecab.sh
cd ../..
