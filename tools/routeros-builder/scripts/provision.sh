#!/bin/bash

set -euo pipefail

# Comment out the following
#      nameservers:
#        addresses: [4.2.2.1, 4.2.2.2, 208.67.220.220]
[ -f /etc/netplan/01-netcfg.yaml ] && sed -i 's/^\s*nameservers:/#&/' /etc/netplan/01-netcfg.yaml
[ -f /etc/netplan/01-netcfg.yaml ] && sed -i 's/^\s*addresses:/#&/' /etc/netplan/01-netcfg.yaml

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
# [!!] As of September 2015 repo doesn't have packages for Ubuntu 20.04 (focal). Temporarily using
# Ubuntu 22.04 (jammy) packages.
# TODO: Remove after fixing main build script
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/hashicorp.asc] https://apt.releases.hashicorp.com jammy main" > \
  /etc/apt/sources.list.d/hashicorp.list

wget -nv https://www.virtualbox.org/download/oracle_vbox_2016.asc -O /usr/share/keyrings/oracle_vbox_2016.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/oracle_vbox_2016.asc] https://download.virtualbox.org/virtualbox/debian $(lsb_release -cs) contrib" > \
  /etc/apt/sources.list.d/virtualbox.list

wget -nv https://download.docker.com/linux/ubuntu/gpg -O /usr/share/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > \
  /etc/apt/sources.list.d/docker.list

echo "Updating apt package information"
DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -qq update
echo "Installing apt packages"
DEBIAN_FRONTEND=noninteractive /usr/bin/apt-get -qq install \
  build-essential python3-venv virtualbox-7.1 packer vagrant docker-ce

echo "Adding vagrant user to docker group"
usermod -a -G docker vagrant
