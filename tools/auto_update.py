#!/usr/bin/env python3

import argparse
import requests
import pathlib
import subprocess


def main(args):
    ros_branches = [
        {
            "name": "routeros",
            "version_file": "LATEST.6fix",
            "version": None,
            "published_version": None
        },
        {
            "name": "routeros-long-term",
            "version_file": "LATEST.6",
            "version": None,
            "published_version": None
        },
        {
            "name": "routeros7",
            "version_file": "NEWEST7.stable",
            "version": None,
            "published_version": None
        }
    ]

    up_to_date = True
    print("Getting current ROS versions")
    for branch in ros_branches:
        # Expected format: 7.2.3 1651504697
        branch["version"] = requests.get(f"http://upgrade.mikrotik.com/routeros/{branch['version_file']}").text.split(" ")[0]
        print(branch["name"] + ": " + branch["version"])

    print("Getting published box versions")
    for branch in ros_branches:
        # Expected format: 6.49.6-0
        branch["published_version"] = requests.get(
            f"https://app.vagrantup.com/api/v1/box/cheretbe/{branch['name']}"
        ).json()["current_version"]["version"].split("-")[0]
        print(branch["name"] + ": " + branch["published_version"])
        if branch["version"] != branch["published_version"]:
            up_to_date = False

    if up_to_date:
        print("All boxes are up to date")
    else:
        print("\nBuilding boxes")
        builder_dir = pathlib.Path(__file__).resolve().parent / "routeros-builder"
        print(f"Using helper VM in '{builder_dir}'")

        try:
            subprocess.check_call(
                ["vagrant", "up"],
                cwd=builder_dir
            )

            print("\nAuthenicating on vagrant cloud")
            subprocess.check_call(
                [
                    "vagrant", "ssh", "--",
                    "vagrant", "cloud", "auth", "login", "-u", "cheretbe", "-t", args.vagrantup_token
                ],
                cwd=builder_dir
            )

            print("\nPublishing boxes")
            for branch in ros_branches:
                if branch["version"] != branch["published_version"]:
                    print("")
                    subprocess.check_call(
                        [
                            "vagrant", "ssh", "--",
                            "ao-env/bin/vagrant-box-publish",
                            "--box-file", f"packer-routeros/build/boxes/{branch['name']}_{branch['version']}.box",
                            "--version-separator", "-", "--batch"
                        ],
                        cwd=builder_dir
                    )
        finally:
            print("\nDestroying helper VM")
            try:
                subprocess.check_call(
                    ["vagrant", "destroy", "-f"],
                    cwd=builder_dir
                )
            except:
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("vagrantup_token", help="app.vagrantup.com token")
    parser.add_argument("tg_bot_token", nargs="?", default="", help="Telegram bot token")
    parser.add_argument("tg_chat_id", nargs="?", default="", help="Telegram chat ID")
    args = parser.parse_args()

    main(args)
