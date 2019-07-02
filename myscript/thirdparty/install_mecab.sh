#!/usr/bin/env bash

cd myscript/thirdparty

# mecab-ko : download
if [ ! -e mecab-0.996-ko-0.9.2.tar.gz ]
then
    wget https://bitbucket.org/eunjeon/mecab-ko/downloads/mecab-0.996-ko-0.9.2.tar.gz
fi
if [ ! -e mecab-0.996-ko-0.9.2/ ]
then
    tar -zxvf mecab-0.996-ko-0.9.2.tar.gz
fi

# mecab-ko : build & install
cd mecab-0.996-ko-0.9.2/
make clean
./configure
make
make check
sudo make install
sudo ldconfig
sudo ldconfig -p | grep /usr/local/lib
cd ../

# mecab-ko-dic : download
if [ ! -e mecab-ko-dic-2.1.1-20180720.tar.gz ]
then
    wget https://bitbucket.org/eunjeon/mecab-ko-dic/downloads/mecab-ko-dic-2.1.1-20180720.tar.gz
fi
if [ ! -e mecab-ko-dic-2.1.1-20180720/ ]
then
    tar -zxvf mecab-ko-dic-2.1.1-20180720.tar.gz
fi

# mecab-ko-dic : build & install
cd mecab-ko-dic-2.1.1-20180720/
make clean
./configure
make
sudo make install
cd ../

# mecab-ko-python
if [ ! -e mecab-python-0.996/ ]
then
    git clone https://bitbucket.org/eunjeon/mecab-python-0.996
    cd mecab-python-0.996/
else
    cd mecab-python-0.996/
    git pull
fi
python setup.py build
python setup.py install
cd ..

rm -rf mecab*
