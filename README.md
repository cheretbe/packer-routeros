[![](https://badgen.net/https/cheretbe.npkn.net/vagrant-ros-version/routeros-long-term)](https://app.vagrantup.com/cheretbe/boxes/routeros-long-term)
[![](https://badgen.net/https/cheretbe.npkn.net/vagrant-ros-version/routeros)](https://app.vagrantup.com/cheretbe/boxes/routeros)
[![](https://badgen.net/https/cheretbe.npkn.net/vagrant-ros-version/routeros7)](https://app.vagrantup.com/cheretbe/boxes/routeros7)

# Mikrotik RouterOS boxes for Vagrant
* https://mikrotik.com
* https://www.vagrantup.com/
* https://packer.io/
* https://www.virtualbox.org/

#### Box URLs
* Version 6 Long-term branch: https://app.vagrantup.com/cheretbe/boxes/routeros-long-term
* Version 6 Stable branch: https://app.vagrantup.com/cheretbe/boxes/routeros
* Version 7 Stable branch: https://app.vagrantup.com/cheretbe/boxes/routeros7

#### Status
:warning:`beta` - The boxes are fully functional, but this project is work-in-progress: breaking changes may be introduced at any time.

#### Plugin
The boxes require `vagrant-routeros` plugin, which is bundled with box file and installed/updated automatically. The plugin is not
stable enough to be published on [rubygems.org](https://rubygems.org/), that's why it is bundled. Eventually it shoud be moved to
a separate repository and published separately.

:warning: ***Important note***: to fix the error *"Unable to resolve dependency: user requested 'vagrant-routeros (= x.x.x)'"* after Vagrant
update, just remove the plugin with the following command:
```shell
vagrant plugin uninstall vagrant-routeros
```
The plugin will reinstall itself automatically when needed.

#### Providers
Currently only `VirtualBox` provider is available.

#### Security
By default the boxes have no firewall rules configured and come with two user accounts:
* `admin` with `vagrant` password
* `vagrant` with password `vagrant` and Vagrant insecure private key authentication enabled

:warning: This unsecure setup is intended for use in isolated testing environments. To secure
a box you need at least change passwords for both users and the private SSH key for `vagrant` user. Disabling
unused services and adding firewall rules is also recommended.<br>
References:
* https://wiki.mikrotik.com/wiki/Manual:User_Manager
* [config.ssh.private_key_path](https://www.vagrantup.com/docs/vagrantfile/ssh_settings.html#config-ssh-private_key_path) parameter
* https://wiki.mikrotik.com/wiki/Use_SSH_to_execute_commands_(DSA_key_login)#Host_to_RouterOS
* https://wiki.mikrotik.com/wiki/Manual:Securing_Your_Router

## Usage
```shell
vagrant init cheretbe/routeros
# or
vagrant init cheretbe/routeros-long-term
# or
vagrant init cheretbe/routeros7

vagrant up
```
`vagrant-routeros` plugin provides two additional provisioners: `routeros_file`, `routeros_command` and guest capability to
change name.<br>
`routeros_file` provisioner allows you to upload a file from the host machine to the guest machine.<br>
`routeros_command` allows you to execute a [RouterOS command](https://wiki.mikrotik.com/wiki/Manual:Scripting)
within the guest machine.

Vagrantfile example that uses this functionality
```ruby
Vagrant.configure("2") do |config|
  config.vm.box = "cheretbe/routeros"
  
  # Change guest name
  config.vm.hostname = "new-name"
  # Execute command
  config.vm.provision "routeros_command", name: "Command test", command: "/system resource print"
  # Upload and execute a script file
  config.vm.provision "routeros_file", name: "Upload test", source: "custom_script.rsc", destination: "custom_script.rsc"
  config.vm.provision "routeros_command", name: "Exec custom script",
    command: "/import custom_script.rsc", check_script_error: true
end
```

#### Accessing the VM from host
1. Interactive SSH session
    * Use `vagrant ssh` command
2. Built-in web interface (WebFig)
    * Find out VM's IP using `vagrant ssh -- /ip address print where interface=host_only` command
    * Note the returned IP and access it from your browser
    * For example if the command has returned `172.28.128.3/24`, use `http://172.28.128.3` as the address
3. Winbox (works fine on Linux using [Wine](https://www.winehq.org/))
    * Download `winbox.exe` or `winbox64.exe` from https://mikrotik.com/download and launch it
    * Option 1 - access by IP address
        * Find out VM's IP using `vagrant ssh -- /ip address print where interface=host_only` command
        * Enter the address in "Connect to" field
    * Option 2 - access using neighbor discovery
        * Select `Neighbors` tab in Winbox connect dialog
        * Find the VM by it's name and click on IP or MAC address column to connect to it. If you click on IP address then IP will be used to connect, but if you click on MAC Address then MAC address will be used to connect to the VM
4. Run commands during provision stage
    * Use `routeros_file`/`routeros_command` provisioners in the Vagrantfile

#### Network configuration
By default two network interfaces are configured in the VM: `NAT` (Vagrant's default) and `Host-only`, named `host_nat` and
`host_only` respectively. Both interfaces configured as DHCP clients, but they **do not receive** default route and DNS server.
This is done to isolate virtual environments from host's physical networks.<br>
If you need Internet access in the VM you can configure `host_nat` adapter using the following RouterOS command:
```
/ip dhcp-client set [find interface="host_nat"] use-peer-dns=yes add-default-route=yes
```
------
Currently guest capability "Configure networks" is not implemented. Therefore you can't configure static IP or DHCP for
additional network interfaces like this:
```diff
- (won't work) config.vm.network "private_network", type: "dhcp", virtualbox__intnet: "vagrant-intnet-1"
- (won't work) config.vm.network "private_network", ip: "172.24.0.1", virtualbox__intnet: "vagrant-intnet-2"
```
Instead you need to disable auto-config in Vagrantfile:
```ruby
config.vm.network "private_network", virtualbox__intnet: "vagrant-intnet-1", auto_config: false
config.vm.network "private_network", virtualbox__intnet: "vagrant-intnet-2", auto_config: false
```
And then configure network addresses using RouterOS command:
```
/ip dhcp-client add disabled=no interface=ether3
/ip address add address=172.24.0.1/24 interface=ether4 network=172.24.0.0
```
------

Interface order in the VM does not always match interface order in the Vagrant file. To work around this issue the boxes contain
a script file named `vagrant_provision_mac_addr.rsc`, that sets two global variables: `vmNICCount` and `vmNICMACs`. `vmNICCount`
is used internally during provision, but you can use `vmNICMACs` to reference interface by index like this:
```
/import vagrant_provision_mac_addr.rsc
:global vmNICMACs
# vmNICMACs array is zero-based
:local eth3MACaddr [:pick $vmNICMACs 2]
:local eth3name [/interface ethernet get [find mac-address="$eth3MACaddr"] name]
/ip address add address=172.24.0.1/24 interface=$eth3name network=172.24.0.0
```

------
:bulb: You can automate RouterOS commands execution by using `vagrant ssh -- <RouterOS command>` command or `routeros_file`/ `routeros_command` provisioners.

## Building the boxes

#### Prepare global build environment (Fedora)

```shell
sudo dnf config-manager --add-repo https://rpm.releases.hashicorp.com/fedora/hashicorp.repo
sudo dnf --assumeyes install @"C Development Tools and Libraries" vagrant-libvirt ruby-devel python3-virtualenv packer
sudo usermod `whoami` --append --groups libvirt
```

#### Use [pyinvoke](http://www.pyinvoke.org/) script to build

```shell
virtualenv venv
source venv/bin/activate
pip3 install -r requirements.txt
# "inv --list" shows other tasks that can be used instead of full build 
inv build
deactivate
```

Go to https://www.vagrantup.com/ and manually publish `build/boxes/routeros*.box` files or
use [vagrant_box_publish.py](https://github.com/cheretbe/ao-env/blob/master/bin/vagrant_box_publish.py)
script
```shell
# Interactive mode
vagrant-box-publish --version-separator - --dry-run
# Batch mode
vagrant-box-publish --box-file build/boxes/routeros_6.48.1.box --version-separator - --batch --dry-run
```


## Notes
```shell
vagrant box add -f mt-test ./build/boxes/routeros.box
```

```ruby
Vagrant.configure("2") do |config|
  config.vm.box = "cheretbe/routeros7"
  # config.vm.box = "cheretbe/routeros"
  # config.vm.box = "cheretbe/routeros-long-term"
  # config.vm.box = "mt-test"
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--groups", "/__vagrant"]
  end
end
```

`~/.vagrant.d/boxes/mt-test/0/virtualbox/Vagrantfile`:
```ruby
# ln -s /home/user/projects/packer-mikrotik/vagrantfile-mikrotik.template template.rb
require (File.dirname(__FILE__) + "/template")
```

```shell
vagrant cloud box show cheretbe/routeros
curl -sS https://app.vagrantup.com/api/v1/box/cheretbe/routeros | jq -r ".current_version.version"
```
