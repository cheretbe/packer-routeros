#!/bin/bash

set -euo pipefail

# Comment out the following
#      nameservers:
#        addresses: [4.2.2.1, 4.2.2.2, 208.67.220.220]
sed -i 's/^\s*nameservers:/#&/' /etc/netplan/01-netcfg.yaml
sed -i 's/^\s*addresses:/#&/' /etc/netplan/01-netcfg.yaml

netplan apply

mkdir -p /etc/systemd/resolved.conf.d
cat <<EOF >/etc/systemd/resolved.conf.d/10-disable-dns-stub.conf
[Resolve]
DNS=
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
# 'vagrant cloud publish' fails on 2.4.0 with an unhelpful message:
# Failed to create box cheretbe/routeros. Vagrant Cloud request failed
# VAGRANT_LOG=info setting shows a weird call to https://vagrantcloud.com/api/v2/api/v1/ URL
# Anyway, we just stick with version 2.3.7-1 for now
DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -qq install \
  build-essential python3-venv vagrant=2.3.7-1 virtualbox-6.1 packer
