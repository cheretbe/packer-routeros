#!/usr/bin/env python3

import sys
import PyInquirer
import requests
import subprocess
import packaging.version

questions = [
    {
        'type': 'list',
        'name': 'branch',
        'message': 'Select a branch',
        "help": "test me",
        'choices': ['routeros', 'routeros-long-term']
    }
]

# answers = PyInquirer.prompt(questions)
# if not answers:
#     sys.exit(1)
# routeros_branch = answers["branch"]
routeros_branch = "routeros-long-term"

if routeros_branch == "routeros-long-term":
    version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6fix"
else:
    version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6"


print("Getting current RouterOS version")
response = requests.get(version_url)
ros_version = response.text.split(" ")[0]
print(ros_version)

questions = [
    {
        "type": "confirm",
        "name": "continue",
        "message": "Do you want to continue with building?",
        "default": True
    }
]
# answers = PyInquirer.prompt(questions)
# if (not answers) or (not answers["continue"]):
#     sys.exit(1)

print("Building...")

# subprocess.check_call("packer build -var \"ros_ver={}\" "
#     "-var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json "
#     "-on-error=ask -force routeros.json".format(ros_version), shell=True)

# [!!!] Remove after debug
routeros_branch = "publish-test"

response = requests.get("https://app.vagrantup.com/api/v1/box/cheretbe/{}".format(routeros_branch))
current_version = response.json()["current_version"]["version"]
print("Currently released version: {}".format(current_version))
current_version, current_subversion = current_version.split("-")

if current_version == ros_version:
    new_version = current_version + "-" + str(int(current_subversion) + 1)
elif packaging.version.parse(ros_version) > packaging.version.parse(current_version):
    new_version = ros_version + "-0"
else:
    raise Exception("Version to be released ({}) is lesser than currently "
        "released ({})".format(ros_version, current_version))

questions = [
    {
        "type": "confirm",
        "name": "continue",
        "message": ("Do you want to release version '{}' of the box?".format(new_version)),
        "default": True
    }
]
answers = PyInquirer.prompt(questions)
if (not answers) or (not answers["continue"]):
    sys.exit(1)

questions = [
    {
        "type": "editor",
        "name": "description",
        "message": "Please enter a version description (Alt+Enter to finish)",
        "default": "**Version description**"
        # 'eargs': {
        #     'editor':'default'
        # }
    }
]
answers = PyInquirer.prompt(questions)
if (not answers) or (not answers["description"]):
    sys.exit(1)

print("Checking Vagrant Cloud login...")

if subprocess.call("vagrant cloud auth login --check", shell=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL) != 0:
    print("You are not currently logged in.")
    print("Please provide your login information to authenticate.")
    subprocess.check_call("vagrant cloud auth login", shell=True)

for line in subprocess.check_output("vagrant cloud auth whoami", shell=True).decode("utf-8").splitlines():
    print(line)

print("Publishing 'cheretbe/{}' as version '{}'".format(routeros_branch, new_version))
subprocess.check_call("vagrant cloud publish 'cheretbe/{}' {} virtualbox "
    "build/boxes/routeros.box "
    "--version-description '{}' "
    "--release --force"
    "".format(routeros_branch, new_version, answers["description"]),
    shell=True)