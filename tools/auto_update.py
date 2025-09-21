#!/usr/bin/env python3

import argparse
import requests
import pathlib
import subprocess


def main(args):
    ros_branches = [
        {
            "name": "routeros-long-term",
            "version_file": "LATEST.6fix",
            "version": None,
            "published_version": None,
        },
        {"name": "routeros", "version_file": "LATEST.6", "version": None, "published_version": None},
        {"name": "routeros7", "version_file": "NEWESTa7.stable", "version": None, "published_version": None},
    ]

    up_to_date = True
    print("Getting current ROS versions")
    for branch in ros_branches:
        # Expected format: 7.2.3 1651504697
        branch["version"] = requests.get(
            f"http://upgrade.mikrotik.com/routeros/{branch['version_file']}"
        ).text.split(" ")[0]
        print(branch["name"] + ": " + branch["version"])

    print("Getting published box versions")
    for branch in ros_branches:
        # Expected format: 6.49.6-0
        branch["published_version"] = (
            requests.get(f"https://app.vagrantup.com/api/v1/box/cheretbe/{branch['name']}")
            .json()["current_version"]["version"]
            .split("-")[0]
        )
        print(branch["name"] + ": " + branch["published_version"])
        if branch["version"] != branch["published_version"]:
            up_to_date = False

    if up_to_date:
        print("All boxes are up to date")
    else:
        print("\nBuilding boxes")
        builder_vm_dir = pathlib.Path(__file__).resolve().parent / "routeros-builder"
        projects_root_dir = pathlib.Path(__file__).resolve().parent.parent

        try:
            if args.use_helper_vm:
                print(f"Using helper VM in '{builder_vm_dir}'")
                subprocess.check_call(("vagrant", "up"), cwd=builder_vm_dir)

            if args.use_helper_vm:
                pass
                subprocess.check_call(
                    (
                        "vagrant",
                        "ssh",
                        "--",
                        "cd packer-routeros; . ~/.cache/build-venv/bin/activate; inv build --batch",
                    ),
                    cwd=builder_vm_dir,
                )
            else:
                subprocess.check_call(
                    ["inv", "build", "--batch"],
                    cwd=projects_root_dir,
                )

            print("\nPublishing boxes")
            for branch in ros_branches:
                if branch["version"] != branch["published_version"]:
                    print("")
                    if args.use_helper_vm:
                        subprocess.check_call(
                            (
                                "vagrant",
                                "ssh",
                                "--",
                                "~/.cache/build-venv/bin/python3",
                                "packer-routeros/tools/box_publish.py",
                                "--box-file",
                                f"packer-routeros/build/boxes/{branch['name']}_{branch['version']}.box",
                                "--version-separator",
                                "-",
                                "--hcp-client-id",
                                args.hcp_client_id,
                                "--hcp-client-secret",
                                args.hcp_client_secret,
                                "--batch",
                                # "--dry-run",
                            ),
                            cwd=builder_vm_dir,
                        )
                    else:
                        subprocess.check_call(
                            (
                                "./tools/box_publish.py",
                                "--box-file",
                                f"build/boxes/{branch['name']}_{branch['version']}.box",
                                "--version-separator",
                                "-",
                                "--batch",
                                # "--dry-run",
                            ),
                            cwd=projects_root_dir,
                        )

        finally:
            if args.use_helper_vm:
                try:
                    print("\nDestroying helper VM")
                    subprocess.check_call(("vagrant", "destroy", "-f"), cwd=builder_vm_dir)
                except:
                    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("hcp_client_id", help="Hashicorp Cloud Portal client ID")
    parser.add_argument("hcp_client_secret", help="Hashicorp Cloud Portal client secret")
    parser.add_argument("tg_bot_token", nargs="?", default="", help="Telegram bot token")
    parser.add_argument("tg_chat_id", nargs="?", default="", help="Telegram chat ID")
    parser.add_argument("--use-helper-vm", action="store_true", default=False, help="Use helper VM")
    args = parser.parse_args()

    main(args)
