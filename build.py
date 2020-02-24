#!/usr/bin/env python3

import sys
import os
import json
import PyInquirer
import requests
import subprocess
import packaging.version

script_dir = os.path.dirname(os.path.realpath(__file__))

def ask_for_confirmation(prompt):
    conf_questions = [
        {
            "type": "confirm",
            "name": "continue",
            "message": prompt,
            "default": True
        }
    ]
    conf_answers = PyInquirer.prompt(conf_questions)
    return (bool(conf_answers) and conf_answers["continue"])

def do_build_plugin():
    vm_dir = os.path.join(script_dir, "tools/vagrant-plugin-builder")
    current_vm_state = ""
    print("Building 'vagrant-routeros' plugin...")
    for line in subprocess.check_output("vagrant status --machine-readable",
            cwd=vm_dir, shell=True).decode("utf-8").splitlines():
        values = line.split(",")
        if len(values) > 3:
            if values[1] == "default" and values[2] == "state":
                current_vm_state = values[3]
    vm_needs_creation = current_vm_state == "not_created"
    vm_needs_start = current_vm_state != "running"
    vm_needs_halt = current_vm_state == "poweroff"

    if vm_needs_creation:
        print("The VM in 'tools/vagrant-plugin-builder' is not created")
        print("This script will create the VM and destroy if after the build")
        if not ask_for_confirmation("Continue?"):
            sys.exit(1)

    if vm_needs_start:
        subprocess.check_call("vagrant up", cwd=vm_dir, shell=True)

    subprocess.check_call("vagrant ssh -- '(source .bash_profile; "
        "cd /mnt/packer-mikrotik/vagrant-plugins-routeros/; "
        "bundle install; "
        "bundle exec rake build)'",
        cwd=vm_dir, shell=True)

    if vm_needs_creation:
        subprocess.check_call("vagrant destroy -f", cwd=vm_dir, shell=True)
    elif vm_needs_halt:
        subprocess.check_call("vagrant halt", cwd=vm_dir, shell=True)


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
# routeros_branch = "routeros-long-term"

if routeros_branch == "routeros-long-term":
    version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6fix"
else:
    version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6"


print("Getting current RouterOS version")
response = requests.get(version_url)
ros_version = response.text.split(" ")[0]
print(ros_version)

if not ask_for_confirmation("Do you want to continue with building?"):
    sys.exit(1)

build_plugin = True
with open(os.path.join(script_dir, "vagrant-plugins-routeros/vagrant_routeros_plugin_version.json")) as f:
    plugin_version = json.load(f)["vagrant_routeros_plugin_version"]
if os.path.isfile(os.path.join(script_dir,
        "vagrant-plugins-routeros/pkg/vagrant-routeros-{}.gem".format(plugin_version))):
    print("'vagrant-routeros' package version {} has alredy been built".format(plugin_version))
    build_plugin = not ask_for_confirmation("Do you want to use existing gem file without rebuilding it?")
if build_plugin:
    do_build_plugin()

box_file_name = "build/boxes/{}_{}.box".format(routeros_branch, ros_version)
build_box = True
if (not build_plugin) and os.path.isfile(box_file_name):
    print("'{}' has alredy been built".format(box_file_name))
    build_box = not ask_for_confirmation("Do you want to use existing box file without rebuilding it?")
if build_box:
    print("Building the box...")
    subprocess.check_call("packer build -var \"ros_ver={}\" "
        "-var \"box_file_name={}\" "
        "-var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json "
        "-on-error=ask -force routeros.json".format(ros_version, box_file_name),
        shell=True)

# routeros_branch = "publish-test"

if not ask_for_confirmation("Publish the box to Vagrant Cloud?"):
    sys.exit(1)

print("Checking Vagrant Cloud login...")

if subprocess.call("vagrant cloud auth login --check", shell=True,
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL) != 0:
    print("You are not currently logged in.")
    print("Please provide your login information to authenticate.")
    subprocess.check_call("vagrant cloud auth login", shell=True)

cloud_user_name = ""
for line in subprocess.check_output("vagrant cloud auth whoami", shell=True).decode("utf-8").splitlines():
    print(line)
    if "Currently logged in as" in line:
        cloud_user_name = line.split(" ")[-1]

if not cloud_user_name:
    raise Exception("Could not detect current Vagrant Cloud user name")

response = requests.get("https://app.vagrantup.com/api/v1/box/{}/{}"
    .format(cloud_user_name, routeros_branch)).json()
if response.get("current_version", ""):
    current_version = response["current_version"]["version"]
    print("Currently released version of '{}/{}': {}"
        .format(cloud_user_name, routeros_branch, current_version))
    current_version, current_subversion = current_version.split("-")

    if current_version == ros_version:
        new_version = current_version + "-" + str(int(current_subversion) + 1)
    elif packaging.version.parse(ros_version) > packaging.version.parse(current_version):
        new_version = ros_version + "-0"
    else:
        raise Exception("Version to be released ({}) is lesser than currently "
            "released ({})".format(ros_version, current_version))
else:
    print("There is no currently released version of '{}/{}'"
        .format(cloud_user_name, routeros_branch))
    new_version = ros_version + "-0"

if not ask_for_confirmation("Do you want to release version '{}' of the box?".format(new_version)):
    sys.exit(1)


questions = [
    {
        "type": "editor",
        "name": "description",
        "message": "Please enter a version description (Alt+Enter to finish)",
        "default": "**Version description**<br>\nhttps://github.com/cheretbe/packer-routeros/blob/master/README.md"
        # 'eargs': {
        #     'editor':'default'
        # }
    }
]
answers = PyInquirer.prompt(questions)
if (not answers) or (not answers["description"]):
    sys.exit(1)

description = answers["description"].replace("\n", "")

print("Publishing '{}/{}' as version '{}'".format(cloud_user_name, routeros_branch, new_version))
subprocess.check_call("vagrant cloud publish '{user}/{box}' {version} virtualbox {file} "
    "--version-description '{description}' "
    "--release --force"
    .format(
        user=cloud_user_name,
        box=routeros_branch,
        version=new_version,
        file=box_file_name,
        description=description),
    shell=True)