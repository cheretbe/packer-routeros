# pylint: disable=missing-module-docstring,missing-function-docstring

import requests
import invoke

def do_build(routeros_branch):
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


@invoke.task(default=True)
def show_help(context):
    """This help message"""
    context.run('invoke --list')
    print("Use --help parameter to view tasks' options")
    # print("Examples:")
    # print("  inv custom --help")

@invoke.task()
def routeros_long_term(context, force_plugin_build=False): # pylint: disable=unused-argument
    """Build RouterOS (long-term)"""
    do_build(routeros_branch="routeros-long-term")

@invoke.task()
def routeros(context, force_plugin_build=False): # pylint: disable=unused-argument
    """Build RouterOS (stable)"""
    do_build(routeros_branch="routeros")
