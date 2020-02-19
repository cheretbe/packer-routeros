#!/usr/bin/env python3

import sys
import PyInquirer
import requests
import subprocess

questions = [
    {
        'type': 'list',
        'name': 'branch',
        'message': 'Select a branch',
        "help": "test me",
        'choices': ['routeros', 'routeros-long-term']
    }
]

answers = PyInquirer.prompt(questions)
if not answers:
    sys.exit(1)
routeros_branch = answers["branch"]

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
answers = PyInquirer.prompt(questions)
if (not answers) or (not answers["continue"]):
    sys.exit(1)

print("Building...")

subprocess.check_call("packer build -var \"ros_ver={}\" "
    "-var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json "
    "-on-error=ask -force routeros.json".format(ros_version), shell=True)