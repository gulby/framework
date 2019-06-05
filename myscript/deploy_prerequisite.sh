#!/usr/bin/env bash

# 기본 패키지 설치
sudo apt update
sudo apt upgrade -y
sudo apt install -y lm-sensors net-tools openssh-server
sudo apt install -y vim screen parallel curl wget	# 맥에서도 brew 로 설치 가능
# 바뀐 커널 적용을 안정적으로 하여 nvidia 그래픽 카드 설치 시 문제가 없도록 리부팅 권장
sudo reboot

# nvidia 그래픽 드라이버 설치
# https://hiseon.me/2018/02/17/install_nvidia_driver/
sudo apt-key adv --fetch-keys http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/7fa2af80.pub
sudo sh -c 'echo "deb http://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64 /" >> /etc/apt/sources.list.d/cuda.list'
sudo sh -c 'echo "deb http://developer.download.nvidia.com/compute/machine-learning/repos/ubuntu1804/x86_64 /" >> /etc/apt/sources.list.d/cuda.list'
sudo apt update
sudo apt install nvidia-driver-410
sudo apt install dkms nvidia-modprobe
sudo reboot

# git 설치
sudo apt install -y git
git config --global user.name $(whoami)
git config --global user.email $(whoami)@deephigh.net
git config --global color.ui auto
git config --global core.quotepath off
git config --global credential.helper store
git config --global pager.branch false

# zsh 설치
# http://programmingskills.net/archives/115
sudo apt install zsh
chsh -s `which zsh`     # 혹은 /etc/passwd 파일 및 /etc/shells 파일을 직접 수정
# 로그아웃/로그인 혹은 리부팅. 이후 최초 터미널 실행 및 2 선택
sh -c "$(curl -fsSL https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
# agnoster 테마로 변경 : 위 URL 참조하여 진행
# 깨지는 폰트 변경 : 위 URL 참조하여 진행. 서버 접속 시엔 할 필요 없음
# 기존에 bash 을 쓰고 있었다면 .bashrc 에 custom 하게 추가된 내용 (미니콘다 등) 을 .zshrc 로 수동으로 추가해야 함

# 미니콘다 설치
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sh Miniconda3-latest-Linux-x86_64.sh
# .bashrc 에 추가해준 내용을, 수동으로 .zshrc 로 추가 후 shell 재시작

# autoenv 설치
git clone git://github.com/kennethreitz/autoenv.git ~/.autoenv
echo "source ~/.autoenv/activate.sh" >> ~/.zshrc
echo "source ~/.autoenv/activate.sh" >> ~/.bashrc
# shell 재시작

# OS 별 모듈설치
if [[ "$OSTYPE" == "darwin"* ]];
then
    # brew 설치
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew install postgresql
    brew services start postgresql
    brew install redis
    brew services start redis
    brew install graphviz
    brew install caskroom/cask/wkhtmltopdf
else
    sudo apt install -y postgresql
    sudo apt install -y redis
    sudo apt install -y graphviz wkhtmltopdf
fi

# docker 설치
sudo apt remove docker docker-engine docker.io containerd runc
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt update
sudo apt install -y docker-ce
sudo docker run hello-world
sudo groupadd docker
sudo usermod -aG docker $(whoami)
sudo reboot
