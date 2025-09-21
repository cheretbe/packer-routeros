#!/bin/bash

set -euo pipefail

# echo "Cloning https://github.com/cheretbe/packer-routeros.git"
# if [ -d packer-routeros ]
# then
#     cd packer-routeros
#     git pull
# else
#     git clone -b develop https://github.com/cheretbe/packer-routeros.git
#     cd packer-routeros
# fi

cd packer-routeros

echo "Activating '.cache/build-venv' virtual environment"
python3 -m venv ~/.cache/build-venv
source ~/.cache/build-venv/bin/activate

echo "--------------------"
echo "Installing pip packages"
echo "--------------------"
pip3 install --progress-bar off --upgrade pip
pip3 install --progress-bar off wheel
pip3 install --progress-bar off -r requirements.txt
# This is to avoid running ao-env installation
# pip3 install --progress-bar off install colorama asciimatics humanfriendly PyInquirer packaging requests

# echo "-----------"
# echo "Building boxes"
# echo "-----------"
# inv build --batch
# #inv routeros --batch

# echo "-----------"
# cd ..
# echo "Cloning https://github.com/cheretbe/ao-env.git"
# if [ -d ao-env ]
# then
#     cd ao-env
#     git pull
# else
#     git clone https://github.com/cheretbe/ao-env.git
#     cd ao-env
# fi
