# pylint: disable=missing-module-docstring,missing-function-docstring
import concurrent.futures
import distutils.version
import itertools
import json
import os
import pathlib
import sys
import types

import invoke
import invoke.program
import requests

script_dir = os.path.dirname(os.path.realpath(__file__))


def ask_for_confirmation(prompt, batch_mode, default):
    if batch_mode:
        print(prompt)
        print(
            "Batch mode is on. Autoselecting default option ({})".format(
                {True: "yes", False: "no"}[default]
            )
        )
        confirmed = default
    else:
        answer = input(f"{prompt} (y/n): ")
        confirmed = answer == "y"
    if not confirmed:
        sys.exit("Cancelled by user")


def get_plugin_file_path():
    with open(
        os.path.join(
            script_dir, "vagrant-plugins-routeros/vagrant_routeros_plugin_version.json"
        )
    ) as ver_f:
        plugin_version = json.load(ver_f)["vagrant_routeros_plugin_version"]
    return os.path.join(
        script_dir,
        f"vagrant-plugins-routeros/pkg/vagrant-routeros-{plugin_version}.gem",
    )


def build_routeros(context, routeros_branch) -> bool:
    if routeros_branch == "routeros-long-term":
        branch_name = "6 (long-term)"
        version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6fix"
    elif routeros_branch == "routeros":
        branch_name = "6 (stable)"
        version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6"
    elif routeros_branch == "routeros7":
        branch_name = "7 (stable)"
        version_url = "http://upgrade.mikrotik.com/routeros/NEWEST7.stable"
    else:
        sys.exit(f"ERROR: Unknow RouterOS branch code: {routeros_branch}")

    print(f"Building RouterOS {branch_name}")

    print("Getting current RouterOS version: ", end="")
    response = requests.get(version_url)
    ros_version = response.text.split(" ")[0]
    print(ros_version)
    ask_for_confirmation(
        "Do you want to continue with building?", context.routeros.batch, True
    )

    plugin_file_path = get_plugin_file_path()
    if not os.path.isfile(plugin_file_path):
        sys.exit(
            f"Plugin gem file '{plugin_file_path}' is missing\n"
            "Use 'inv plugin' to build it"
        )

    box_file_name = f"build/boxes/{routeros_branch}_{ros_version}.box"
    if os.path.isfile(box_file_name):
        print(f"'{box_file_name}' has alredy been built")
        ask_for_confirmation("Do you want to rebuild it?", context.routeros.batch, True)

    packer_error_action = "cleanup" if context.routeros.batch else "ask"
    print("Building the box...")
    context.run(
        f'packer build -var "ros_ver={ros_version}" '
        f'-var "box_file_name={box_file_name}" '
        "-var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json "
        f"-on-error={packer_error_action} -force routeros.pkr.hcl",
        echo=True,
    )

    description_md = pathlib.Path(box_file_name).with_suffix(".md")
    print(f"Writing '{description_md}'")
    with open(description_md, "w") as desc_f:
        desc_f.write(
            f"**Updated ROS to version {ros_version}**<br>"
            "https://github.com/cheretbe/packer-routeros/blob/master/README.md"
        )

    return True


def build_plugin(context):
    print("Building 'vagrant-routeros' plugin...")
    vm_dir = os.path.join(script_dir, "tools/vagrant-plugin-builder")
    print(f"Using helper VM in '{vm_dir}'")
    current_vm_state = ""
    with context.cd(vm_dir):
        run_result = context.run(command="vagrant status --machine-readable", hide=True)
    for line in run_result.stdout.splitlines():
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
        ask_for_confirmation("Continue?", context.routeros.batch, True)

    if vm_needs_start:
        with context.cd(vm_dir):
            context.run("vagrant up", pty=True)

    with context.cd(vm_dir):
        context.run(
            "vagrant ssh -- '(source .bash_profile; "
            "cd /mnt/packer-mikrotik/vagrant-plugins-routeros/; "
            "sudo BUNDLE_SILENCE_ROOT_WARNING=true bundle install; "
            "bundle exec rake build)'"
        )

    if vm_needs_creation:
        with context.cd(vm_dir):
            context.run("vagrant destroy -f")
    elif vm_needs_halt:
        with context.cd(vm_dir):
            context.run("vagrant halt")


def remove_test_boxes(context):
    for line in context.run("vagrant box list", hide=True).stdout.splitlines():
        box_name = line.split(" ")[0]
        if box_name in (
            "packer_test_routeros",
            "packer_test_routeros-long-term",
            "packer_test_routeros7",
        ):
            context.run(f"vagrant box remove -f {box_name}", pty=True)


def do_cleanup(context):
    print("Cleaning up...")

    remove_test_boxes(context)

    files_2del = (pathlib.Path(script_dir) / "build" / "boxes").glob("*.box")
    files_2del = itertools.chain(
        files_2del, (pathlib.Path(script_dir) / "build" / "boxes").glob("*.md")
    )
    files_2del = itertools.chain(
        files_2del,
        (pathlib.Path(script_dir) / "vagrant-plugins-routeros" / "pkg").glob("*.gem"),
    )
    files_2del = itertools.chain(
        files_2del, (pathlib.Path(script_dir) / "packer_cache").rglob("*")
    )

    for f_2del in files_2del:
        if f_2del.is_file():
            print(f"  Deleting {f_2del}")
            f_2del.unlink()


def register_test_box(context, routeros_branch):
    boxes_dir = pathlib.Path(script_dir) / "build" / "boxes"
    box_versions = [
        item.stem.split("_")[1] for item in boxes_dir.glob(f"{routeros_branch}_*.box")
    ]
    if len(box_versions) == 0:
        sys.exit(
            f"Couldn't find files matching pattern 'build/boxes/{routeros_branch}"
            f"_*.box'. Use 'inv {routeros_branch}' to build a box"
        )
    box_file = (
        f"{routeros_branch}_"
        + max(box_versions, key=distutils.version.LooseVersion)
        + ".box"
    )
    box_file = str(boxes_dir / box_file)
    context.run(f"vagrant box add packer_test_{routeros_branch} {box_file}", pty=True)


def test_ping(context, vm_name, ping_target):
    print(f"Pinging {ping_target} from {vm_name}")
    ping_output = context.run(
        f"vagrant ssh {vm_name} -- /ping count=3 {ping_target}"
    ).stdout
    assert "received=3" in ping_output
    assert "packet-loss=0%" in ping_output


@invoke.task(default=True)
def show_help(context):
    """This help message"""
    context.run("invoke --list")
    print("Use --help parameter to view task's options")
    print("Examples:")
    print("  inv build --help")
    print("  inv build --batch")
    print("  inv routeros")
    print("  inv plugin --batch")


@invoke.task()
def cleanup(context):
    """Delete build artefacts and temporary files"""
    do_cleanup(context)


@invoke.task()
def test(context):
    """Register temporary vagrant boxes and run some tests against them"""
    print("Removing existing test boxes...")
    remove_test_boxes(context)

    print("Registering test boxes...")
    register_test_box(context, "routeros")
    register_test_box(context, "routeros-long-term")
    register_test_box(context, "routeros7")

    print("Running tests...")
    with context.cd(str(pathlib.Path(script_dir) / "tests" / "vagrant_local")):
        context.run("vagrant up", pty=True)

        test_ping(context, "host1", "192.168.199.11")
        test_ping(context, "host1", "192.168.199.12")

        test_ping(context, "host2", "192.168.199.10")
        test_ping(context, "host2", "192.168.199.12")

        test_ping(context, "host3", "192.168.199.10")
        test_ping(context, "host3", "192.168.199.11")

        context.run("vagrant halt", pty=True)
        context.run("vagrant destroy -f", pty=True)

    print("Removing test boxes...")
    remove_test_boxes(context)


@invoke.task(help={"batch": "Batch mode (disables interactive prompts)"})
def build(context, batch=False):
    """Build all"""

    context.routeros.batch = batch
    do_cleanup(context)
    build_plugin(context)
    branches = ["routeros-long-term", "routeros", "routeros7"]
    if batch:
        build_error = False
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(branches)
        ) as executor:
            future_to_branch = {
                executor.submit(build_routeros, context, branch): branch
                for branch in branches
            }
            for future in concurrent.futures.as_completed(future_to_branch):
                branch = future_to_branch[future]
                try:
                    if not future.result():
                        build_error = True
                except Exception:
                    build_error = True
        if build_error:
            sys.exit("At least one build branch had an error, terminating.")
    else:
        for branch in branches:
            build_routeros(context, routeros_branch=branch)
    test(context)


@invoke.task(help={"batch": "Batch mode (disables interactive prompts)"})
def routeros_long_term(context, batch=False):
    """Build RouterOS (long-term)"""

    context.routeros.batch = batch
    build_routeros(context, routeros_branch="routeros-long-term")


@invoke.task(help={"batch": "Batch mode (disables interactive prompts)"})
def routeros(context, batch=False):
    """Build RouterOS (stable)"""

    context.routeros.batch = batch
    build_routeros(context, routeros_branch="routeros")


@invoke.task(help={"batch": "Batch mode (disables interactive prompts)"})
def routeros7(context, batch=False):
    """Build RouterOS 7 (stable)"""

    context.routeros.batch = batch
    build_routeros(context, routeros_branch="routeros7")


@invoke.task(help={"batch": "Batch mode (disables interactive prompts)"})
def plugin(context, batch=False):
    """Build 'vagrant-routeros' plugin"""

    context.routeros.batch = batch
    build_plugin(context)


@invoke.task()
def outdated(context):  # pylint: disable=unused-argument
    """Check if currently published box versions are up to date"""

    ros_version_info = [
        types.SimpleNamespace(
            branch_name="6 (long-term)",
            version_url="http://upgrade.mikrotik.com/routeros/LATEST.6fix",
            box_name="cheretbe/routeros-long-term",
            box_url="https://app.vagrantup.com/api/v1/box/cheretbe/routeros-long-term",
        ),
        types.SimpleNamespace(
            branch_name="6 (stable)",
            version_url="http://upgrade.mikrotik.com/routeros/LATEST.6",
            box_name="cheretbe/routeros",
            box_url="https://app.vagrantup.com/api/v1/box/cheretbe/routeros",
        ),
        types.SimpleNamespace(
            branch_name="7 (stable)",
            version_url="http://upgrade.mikrotik.com/routeros/NEWEST7.stable",
            box_name="cheretbe/routeros7",
            box_url="https://app.vagrantup.com/api/v1/box/cheretbe/routeros7",
        ),
    ]

    for ros_version in ros_version_info:
        print(f"Checking RouterOS {ros_version.branch_name} version")
        current_version = distutils.version.LooseVersion(
            requests.get(ros_version.version_url).text.split(" ")[0]
        )
        box_version = requests.get(ros_version.box_url).json()["current_version"][
            "version"
        ]
        box_os_version = distutils.version.LooseVersion(box_version.split("-")[0])

        if box_os_version == current_version:
            print(
                f"Published version {box_version} of '{ros_version.box_name}' is up to date"
            )
        elif current_version > box_os_version:
            print(
                f"[!] '{ros_version.box_name}' box version {box_version} needs "
                f"an upgrade to version {current_version}"
            )
        else:
            print(
                f"[!] WARNING: '{ros_version.box_name}' box version {box_version} "
                f"is greater than currently published version {current_version}"
            )


invoke.main.program.config.update({"routeros": {"batch": False}})
