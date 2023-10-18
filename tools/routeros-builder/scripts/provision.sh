#!/bin/bash

set -euo pipefail

mkdir -p /etc/systemd/resolved.conf.d
cat <<EOF >/etc/systemd/resolved.conf.d/10-disable-dns-stub.conf
[Resolve]
DNSStubListener=no
EOF
systemctl restart systemd-resolved.service
ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf

wget -nv https://apt.releases.hashicorp.com/gpg -O /usr/share/keyrings/hashicorp.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp.asc] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > \
  /etc/apt/sources.list.d/hashicorp.list

wget -nv https://www.virtualbox.org/download/oracle_vbox_2016.asc -O /usr/share/keyrings/oracle_vbox_2016.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/oracle_vbox_2016.asc] https://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" > \
  /etc/apt/sources.list.d/virtualbox.list

echo "Updating apt package information"
DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -qq update
echo "Installing apt packages"
DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -qq install \
  build-essential python3-venv vagrant virtualbox-6.1 packer

echo "Cloning https://github.com/cheretbe/packer-routeros.git"
if [ -d packer-routeros ]
then
    cd packer-routeros
    git pull
else
    git clone https://github.com/cheretbe/packer-routeros.git
    cd packer-routeros
fi


echo "Activate '.venv' virtual environment"
python3 -m venv ~/.venv
source ~/.venv/bin/activate

echo "Install pip packages"
echo "--------------------"
pip3 install --progress-bar off --upgrade pip
pip3 install --progress-bar off --root-user-action=ignore wheel
pip3 install --progress-bar off --root-user-action=ignore -r requirements.txt

echo "Build boxes"
echo "-----------"
inv build --batch