# pylint: disable=missing-module-docstring,missing-function-docstring
import distutils.version
import json
import os
import pathlib
import shutil
import sys
import types

import invoke.program
import jinja2
import requests

script_dir = os.path.dirname(os.path.realpath(__file__))


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


def build_routeros(context, routeros_branch="*"):
    print(f"Building RouterOS branch: {routeros_branch}")
    branch_filter = (
        routeros_branch if (routeros_branch == "*") else f"{routeros_branch}.*"
    )

    plugin_file_path = get_plugin_file_path()
    if not os.path.isfile(plugin_file_path):
        sys.exit(
            f"Plugin gem file '{plugin_file_path}' is missing\n"
            "Use 'inv plugin' to build it"
        )

    context.run(
        f"packer build"
        " -var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json"
        f' -var "box_path=build/boxes"'
        f' -only="{branch_filter}"'
        f" -on-error=abort -force routeros.pkr.hcl",
        echo=True,
    )


def build_plugin(context):
    print("Building 'vagrant-routeros' plugin...")
    with context.cd(os.path.join(script_dir, "vagrant-plugins-routeros")):
        context.run(
            "bundle config --local path bundle && bundle install && bundle exec rake build"
        )


def do_cleanup(context):
    print("Cleaning up...")

    remove_test_boxes(context)

    for directory in [
        pathlib.Path(script_dir) / "build",
        pathlib.Path(script_dir) / "vagrant-plugins-routeros" / ".bundle",
        pathlib.Path(script_dir) / "vagrant-plugins-routeros" / "bundle",
        pathlib.Path(script_dir) / "vagrant-plugins-routeros" / "pkg",
    ]:
        if directory.is_dir():
            print(f"  Deleting {directory}")
            shutil.rmtree(directory)

    for file in [
        pathlib.Path(script_dir) / "vagrant-plugins-routeros" / "Gemfile.lock"
    ]:
        if file.is_file():
            print(f"  Deleting {file}")
            file.unlink()


def build_template(context, output_filename):
    print("Building Packer HCL2 template")
    with open(f"{output_filename}.j2", "r") as file:
        j2 = file.read()
    hcl2 = jinja2.Template(j2).render(
        {
            "versions": [branch["version"] for branch in context.routeros.branches],
            "branches": context.routeros.branches,
        }
    )
    with open(output_filename, "w") as file:
        file.write(hcl2)


def register_test_box(context, routeros_branch):
    boxes_dir = pathlib.Path(script_dir) / "build" / "boxes"
    box_versions = [
        item.stem.split("_")[2] for item in boxes_dir.glob(f"{routeros_branch}_*.box")
    ]
    if len(box_versions) == 0:
        sys.exit(
            f"Couldn't find files matching pattern 'build/boxes/{routeros_branch}"
            f"_*.box'. Use 'inv {routeros_branch}' to build a box"
        )
    box_file = (
        f"{routeros_branch}_*_"
        + max(box_versions, key=distutils.version.LooseVersion)
        + ".box"
    )
    box_file = str(boxes_dir / box_file)
    context.run(f"vagrant box add packer_test_{routeros_branch} {box_file}", pty=True)


def remove_test_boxes(context):
    packer_test_boxes = [
        f"packer_test_{branch['name']}" for branch in context.routeros.branches
    ]
    for line in context.run("vagrant box list", hide=True).stdout.splitlines():
        box_name = line.split(" ")[0]
        if box_name in packer_test_boxes:
            context.run(f"vagrant box remove -f {box_name}", pty=True)


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
    print("Examples:")
    print("  inv plugin")
    print("  inv build")
    print("  inv routeros-long-term")


@invoke.task()
def cleanup(context):
    """Delete build artifacts and temporary files"""

    do_cleanup(context)


@invoke.task()
def test(context):
    """Register temporary vagrant boxes and run some tests against them"""

    print("Removing existing test boxes...")
    remove_test_boxes(context)

    print("Registering test boxes...")
    for branch in context.routeros.branches:
        register_test_box(context, branch["name"])

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


@invoke.task()
def template(context):
    """Generate the Packer HCL2 template"""

    build_template(context, "routeros.pkr.hcl")


@invoke.task(pre=[template])
def build(context):
    """Build all"""

    do_cleanup(context)
    build_plugin(context)
    build_routeros(context)
    test(context)


@invoke.task(pre=[template])
def routeros_long_term(context):
    """Build RouterOS (long-term)"""

    build_routeros(context, routeros_branch="routeros-long-term")


@invoke.task(pre=[template])
def routeros(context):
    """Build RouterOS (stable)"""

    build_routeros(context, routeros_branch="routeros")


@invoke.task(pre=[template])
def routeros7(context):
    """Build RouterOS 7 (stable)"""

    build_routeros(context, routeros_branch="routeros7")


@invoke.task()
def plugin(context):
    """Build 'vagrant-routeros' plugin"""

    build_plugin(context)


@invoke.task()
def outdated(context):  # pylint: disable=unused-argument
    """Check if currently published box versions are up to date"""

    ros_version_info = []
    for branch in context.routeros.branches:
        ros_version_info.append(
            types.SimpleNamespace(
                branch_name=branch["name"],
                version=branch["version"],
                box_name=f"cheretbe/{branch['name']}",
                box_url=f"https://app.vagrantup.com/api/v1/box/cheretbe/{branch['name']}",
            )
        )
    for ros_version in ros_version_info:
        print(f"Checking RouterOS {ros_version.branch_name} version")
        current_version = distutils.version.LooseVersion(ros_version.version)
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


def get_branches():
    branches = [
        {
            "name": "routeros-long-term",
            "url": "http://upgrade.mikrotik.com/routeros/LATEST.6fix",
            "description": "6 (long-term)",
        },
        {
            "name": "routeros",
            "url": "http://upgrade.mikrotik.com/routeros/LATEST.6",
            "description": "6 (stable)",
        },
        {
            "name": "routeros7",
            "url": "http://upgrade.mikrotik.com/routeros/NEWEST7.stable",
            "description": "7 (stable)",
        },
    ]
    for branch in branches:
        response = requests.get(branch["url"])
        branch["version"] = response.text.split(" ")[0]
    return branches


invoke.main.program.config.update({"routeros": {"branches": get_branches()}})
