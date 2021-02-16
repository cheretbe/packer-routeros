# pylint: disable=missing-module-docstring,missing-function-docstring
import os
import sys
import json
import pathlib
import itertools
import requests
import invoke
import invoke.program
import PyInquirer

script_dir = os.path.dirname(os.path.realpath(__file__))

def ask_for_confirmation(prompt, batch_mode, default):
    if batch_mode:
        print(prompt)
        print("Batch mode is on. Autoselecting default option ({})".format(
            {True: "yes", False: "no"}[default]
        ))
        confirmed = default
    else:
        conf_questions = [
            {
                "type": "confirm",
                "name": "continue",
                "message": prompt,
                "default": True
            }
        ]
        conf_answers = PyInquirer.prompt(conf_questions)
        confirmed = bool(conf_answers) and conf_answers["continue"]
    if not confirmed:
        sys.exit("Cancelled by user")


def get_plugin_file_path():
    with open(
        os.path.join(script_dir, "vagrant-plugins-routeros/vagrant_routeros_plugin_version.json")
    ) as ver_f:
        plugin_version = json.load(ver_f)["vagrant_routeros_plugin_version"]
    return os.path.join(
        script_dir,
        "vagrant-plugins-routeros/pkg/vagrant-routeros-{}.gem".format(plugin_version)
    )

def build_routeros(context, routeros_branch):
    if routeros_branch == "routeros-long-term":
        branch_name = "long-term"
        version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6fix"
    else:
        branch_name = "stable"
        version_url = "http://upgrade.mikrotik.com/routeros/LATEST.6"

    print("Building RouterOS ({})".format(branch_name))

    print("Getting current RouterOS version")
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

    box_file_name = "build/boxes/{}_{}.box".format(routeros_branch, ros_version)
    if os.path.isfile(box_file_name):
        print("'{}' has alredy been built".format(box_file_name))
        ask_for_confirmation(
            "Do you want to rebuild it?", context.routeros.batch, True
        )

    packer_error_action = "cleanup" if context.routeros.batch else "ask"
    print("Building the box...")
    context.run(
        f"packer build -var \"ros_ver={ros_version}\" "
        f"-var \"box_file_name={box_file_name}\" "
        "-var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json "
        f"-on-error={packer_error_action} -force routeros.json",
        echo=True
    )

    # TODO: create markdown file here
    # jinja2.Environment(undefined=jinja2.StrictUndefined).from_string("Hello {{ something1 }}!").render(something="World")


def build_plugin(context):
    print("Building 'vagrant-routeros' plugin...")
    vm_dir = os.path.join(script_dir, "tools/vagrant-plugin-builder")
    print(f"Using helper VM in '{vm_dir}'")
    current_vm_state = ""
    with context.cd(vm_dir):
        run_result = context.run(
            command="vagrant status --machine-readable", hide=True
        )
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
            context.run("vagrant up")

    with context.cd(vm_dir):
        context.run("vagrant ssh -- '(source .bash_profile; "
            "cd /mnt/packer-mikrotik/vagrant-plugins-routeros/; "
            "bundle install; "
            "bundle exec rake build)'"
        )

    if vm_needs_creation:
        with context.cd(vm_dir):
            context.run("vagrant destroy -f")
    elif vm_needs_halt:
        with context.cd(vm_dir):
            context.run("vagrant halt")

def do_cleanup():
    print("Cleaning up...")

    files_2del = (pathlib.Path(script_dir) / "build" / "boxes").glob("*.box")
    files_2del = itertools.chain(
        files_2del,
        (pathlib.Path(script_dir) / "vagrant-plugins-routeros" / "pkg").glob("*.gem")
    )
    files_2del = itertools.chain(
        files_2del,
        (pathlib.Path(script_dir) / "packer_cache").glob("*.*")
    )

    for f_2del in files_2del:
        print(f"  Deleting {f_2del}")
        f_2del.unlink()


@invoke.task(default=True)
def show_help(context):
    """This help message"""
    context.run('invoke --list')
    print("Use --help parameter to view task's options")
    print("Examples:")
    print("  inv build --help")
    print("  inv build --batch")
    print("  inv routeros")
    print("  inv plugin --batch")

@invoke.task()
def cleanup(context): # pylint: disable=unused-argument
    """Delete build artefacts and temporary files"""
    do_cleanup()

@invoke.task(help={"batch": "Batch mode (disables interactive prompts)"})
def build(context, batch=False):
    """Build all"""

    context.routeros.batch = batch
    do_cleanup()
    build_plugin(context)
    build_routeros(context, routeros_branch="routeros-long-term")
    build_routeros(context, routeros_branch="routeros")

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
def plugin(context, batch=False):
    """Build 'vagrant-routeros' plugin"""

    context.routeros.batch = batch
    build_plugin(context)

invoke.main.program.config.update(
    {
        "routeros": {
            "batch": False
        }
    }
)
