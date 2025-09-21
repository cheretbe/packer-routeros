#!/usr/bin/env python3

# pylint: disable=invalid-name,missing-module-docstring,missing-function-docstring

import sys
import os
import argparse
import datetime
import pathlib
import subprocess
import requests
import PyInquirer
import packaging.version
import routeros_utils


def ask_for_confirmation(prompt, batch_mode, default):
    if batch_mode:
        print(prompt)
        print(
            "Batch mode is on. Autoselecting default option ({})".format({True: "yes", False: "no"}[default])
        )
        confirmed = default
    else:
        conf_questions = [
            {
                "type": "confirm",
                "name": "continue",
                "message": prompt,
                "default": True,
                "keyboard_interrupt_msg": "",
            }
        ]
        conf_answers = PyInquirer.prompt(conf_questions, keyboard_interrupt_msg="")
        confirmed = bool(conf_answers) and conf_answers["continue"]
    if not confirmed:
        sys.exit("Cancelled by user")


def inc_version_release(new_base_version, current_version, separator):
    # print(current_version.split(separator))
    print(current_version.rsplit(separator, maxsplit=1))
    current_base_version, current_subversion = current_version.rsplit(separator, maxsplit=1)
    if current_base_version == new_base_version:
        new_version = current_base_version + separator + str(int(current_subversion) + 1)
    elif routeros_utils.normalize_routeros_version(
        new_base_version
    ) > routeros_utils.normalize_routeros_version(current_base_version):
        new_version = new_base_version + separator + "0"
    else:
        sys.exit(
            f"Version to be released ({new_base_version}) is lower than currently "
            f"released ({current_base_version})"
        )
    return new_version


def select_box_file(batch_mode):
    box_files = sorted(pathlib.Path().rglob("*.box"))
    if len(box_files) == 0:
        sys.exit("Can't find any *.box files in current directory and subdirectories")
    if len(box_files) == 1:
        return str(box_files[0])
    if batch_mode:
        sys.exit("More than one box file has been found. Will not display selection " "dialog in batch mode")
    answers = PyInquirer.prompt(
        questions=[
            {
                "type": "list",
                "name": "boxfile",
                "message": "Select a box file to publish",
                "choices": [str(i) for i in box_files],
            }
        ],
        keyboard_interrupt_msg="",
    )
    if not answers:
        sys.exit("Cancelled by user")
    return str(answers["boxfile"])


# By default login token is in ~/.vagrant.d/data/vagrant_login_token
# [!] Make sure there are no leading spaces when copypasting the following
# curl -s "https://vagrantcloud.com/api/v1/authenticate?access_token="\
# "$(cat ~/.vagrant.d/data/vagrant_login_token)" | jq -r .user.username
def check_vagrant_cloud_login(batch_mode):
    print("Checking Vagrant Cloud login...")

    if (
        subprocess.call(
            "vagrant cloud auth login --check",
            shell=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        != 0
    ):
        print("You are not currently logged in.")
        sys.exit(
            "Set HCP_CLIENT_ID, HCP_CLIENT_SECRET env variables "
            "or use --hcp-client-id --hcp-client-secret options for cloud auth to work"
        )


def get_box_name_and_version(box_file, explicit_name, explicit_version):
    if (not explicit_name) or (not explicit_version):
        box_file_name = pathlib.Path(box_file).stem
        idx = len(box_file_name) - 1
        while idx >= 0:
            token = box_file_name[idx]
            if not (token.isdigit() or (token in [".", "-"])):
                break
            idx -= 1
        if idx == len(box_file_name) - 1:
            box_name = box_file_name
            box_version = ""
        else:
            box_name = box_file_name[0:idx]
            box_version = box_file_name[idx + 1 :]
    if explicit_name:
        box_name = explicit_name
    if explicit_version:
        box_version = explicit_version
    if not box_version:
        print("Box version is not specified and has not been detected from the file name")
        box_version = datetime.datetime.now().strftime("%Y%m%d")
        print(f"Using {box_version} as a box version")

    return [box_name, box_version]


def get_box_description(batch_mode, is_new_box):
    box_description = ""
    if os.path.isfile("box_description.md"):
        print("Reading box description from 'box_description.md'")
        with open("box_description.md", "r") as desc_f:
            box_description = desc_f.read().strip("\n")

    # For a newly created box there has to be a description
    if is_new_box:
        if not box_description:
            if batch_mode:
                sys.exit(
                    "'box_description.md' is missing. Will not create a new box "
                    "without a description in batch mode"
                )
            answers = PyInquirer.prompt(
                questions=[
                    {
                        "type": "editor",
                        "name": "box_description",
                        "message": "Please enter box description (Alt+Enter to finish)\n",
                        "default": box_description,
                    }
                ],
                keyboard_interrupt_msg="",
            )
            if not answers:
                sys.exit("Cancelled by user")
            box_description = answers["box_description"]
    return box_description


def get_current_cloud_box_version(cloud_user_name, box_name):
    print("Getting currently released version info")
    response = requests.get(f"https://app.vagrantup.com/api/v1/box/{cloud_user_name}/{box_name}").json()
    if response.get("current_version", ""):
        current_version = response["current_version"]["version"]
        print(f"Currently released version of '{cloud_user_name}/{box_name}': {current_version}")
    else:
        print(f"There is no currently released version of '{cloud_user_name}/{box_name}'")
        current_version = ""
    return current_version


def get_version_description(box_file, batch_mode):
    description_md = pathlib.Path(box_file).with_suffix(".md")
    if description_md.exists():
        print(f"Reading version description from '{str(description_md)}'")
        with open(str(description_md), "r") as desc_f:
            version_description = desc_f.read().strip("\n")
    else:
        version_description = datetime.datetime.now().strftime("**%d.%m.%Y update**")

    if not batch_mode:
        answers = PyInquirer.prompt(
            questions=[
                {
                    "type": "editor",
                    "name": "version_description",
                    "message": "Please enter a version description (Alt+Enter to finish)\n",
                    "default": version_description,
                }
            ],
            keyboard_interrupt_msg="",
        )
        if not answers:
            sys.exit("Cancelled by user")
        version_description = answers["version_description"]

    return version_description


def publish_box(  # pylint: disable=too-many-arguments
    box_file, cloud_user_name, box_name, box_version, box_description, version_description, dry_run_mode
):
    print(f"Publishing '{box_file}' as '{cloud_user_name}/{box_name}'version {box_version}")
    vagrant_parameters = [
        "vagrant",
        "cloud",
        "publish",
        f"{cloud_user_name}/{box_name}",
        box_version,
        "virtualbox",
        box_file,
        "--version-description",
        version_description,
        "--release",
        "--force",
    ]
    if box_description:
        vagrant_parameters += ["--short-description", box_description]
    if dry_run_mode:
        print("Dry-run mode is on. Skipping vagrant cloud call")
        print(vagrant_parameters)
    else:
        subprocess.check_call(vagrant_parameters)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Publish boxes to Vagrant Cloud")
    parser.add_argument(
        "box_ver",
        nargs="?",
        default="",
        help="Box base version (optional, yyyymmdd will be used by default, where yyyy "
        "is current year, mm is current month, dd is current day)",
    )
    parser.add_argument("-f", "--box-file", default="", help="Path to a box file to publish")
    parser.add_argument(
        "-u",
        "--username",
        default="cheretbe",
        help="Vagrant Cloud user name (default: cheretbe)",
    )
    parser.add_argument(
        "-n",
        "--box-name",
        default="",
        help="Vagrant Cloud box name. Will try autodetection from box file name if not set",
    )
    parser.add_argument(
        "-s",
        "--version-separator",
        default=".",
        help="Separator. A character, that separates box base version from a box " "release (default: '.')",
    )
    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        default=False,
        help="Batch mode (disables all interactive prompts)",
    )
    parser.add_argument(
        "--hcp-client-id",
        help="Hashicorp Cloud Portal client ID",
    )
    parser.add_argument(
        "--hcp-client-secret",
        help="Hashicorp Cloud Portal client secret",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Dry run mode (doesn't actually publish a box, just echoes vagrant "
            "cloud command to be called)"
        ),
    )
    return parser.parse_args()


def main():
    options = parse_arguments()

    if options.box_file == "":
        options.box_file = select_box_file(batch_mode=options.batch)
    print(f"Box file name: {options.box_file}")
    if not pathlib.Path(options.box_file).is_file():
        sys.exit(f"File doesn't exist: {options.box_file}")
    cloud_user_name = options.username

    if options.hcp_client_id:
        os.environ["HCP_CLIENT_ID"] = options.hcp_client_id
    if options.hcp_client_secret:
        os.environ["HCP_CLIENT_SECRET"] = options.hcp_client_secret
    check_vagrant_cloud_login(options.batch)

    box_name, box_version = get_box_name_and_version(
        box_file=options.box_file, explicit_name=options.box_name, explicit_version=options.box_ver
    )

    print(f"Publishing '{cloud_user_name}/{box_name}' {box_version}")

    current_version = get_current_cloud_box_version(cloud_user_name, box_name)
    if current_version:
        new_version = inc_version_release(
            new_base_version=box_version,
            current_version=current_version,
            separator=options.version_separator,
        )
    else:
        new_version = box_version + options.version_separator + "0"

    box_description = get_box_description(batch_mode=options.batch, is_new_box=(not bool(current_version)))

    version_description = get_version_description(options.box_file, options.batch)

    if current_version:
        current_version_info = f", replacing currenly released version {current_version}"
    else:
        current_version_info = f", creating a new box\nBox description: {box_description}"
    print(
        f"This will release '{options.box_file}' as '{cloud_user_name}/{box_name}' "
        f"version {new_version}" + current_version_info + f"\nVersion description: {version_description}"
    )
    ask_for_confirmation(prompt="Do you want to continue?", batch_mode=options.batch, default=True)

    publish_box(
        box_file=options.box_file,
        cloud_user_name=cloud_user_name,
        box_name=box_name,
        box_version=new_version,
        box_description=box_description,
        version_description=version_description,
        dry_run_mode=options.dry_run,
    )


if __name__ == "__main__":
    main()
