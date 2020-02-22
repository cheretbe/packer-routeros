# Mikrotik RouterOS boxes for Vagrant
* https://mikrotik.com
* https://www.vagrantup.com/
* https://packer.io/

#### Box URLs
* Long-term branch: https://app.vagrantup.com/cheretbe/boxes/routeros-long-term
* Stable branch: https://app.vagrantup.com/cheretbe/boxes/routeros

#### Status
:warning:`beta` - The boxes are fully functional, but this project is work-in-progress: breaking changes may be introduced at any time.

#### Plugin
The boxes require `vagrant-routeros` plugin, which is bundled with box file and installed/updated automatically. The plugin is not
stable enough to be published on [rubygems.org](https://rubygems.org/), that's why it is bundled. Eventually it shoud be moved to
a separate repository and published separately.

## Usage
```shell
vagrant init cheretbe/routeros
# or
vagrant init cheretbe/routeros-long-term

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
  config.vm.provision "routeros_command", name: "Exec custom script", command: "/import custom_script.rsc"
end
```

## Building the boxes

#### Option 1. Use interactive script.

```shell
./build.py
```

The script needs Python3 installed and uses `PyInquirer` package. It can be
installed using pip
```shell
pip3 install PyInquirer
```

#### Option 2. Manual build.
1. Build `vagrant-routeros` plugin
```shell
cd tools/vagrant-plugin-builder
vagrant up && vagrant ssh
cd /mnt/packer-mikrotik/vagrant-plugins-routeros/
bundle install && bundle exec rake build
logout
cd ../..
```

2. Get current RouterOS version
```shell
# Stable branch
ros_version=$(curl -s http://upgrade.mikrotik.com/routeros/LATEST.6 | cut -d' ' -f1)
# long-term branch
ros_version=$(curl -s http://upgrade.mikrotik.com/routeros/LATEST.6fix | cut -d' ' -f1)

echo ${ros_version}
```

3. Build the box
```shell
rm packer_cache -rf; packer build -var ros_ver=${ros_version} \
  -var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json \
  -on-error=ask -force routeros.json
```

4. Go to https://www.vagrantup.com/ and manually publish `build/boxes/routeros.box`

#### Windows
```batch
powershell '[System.Text.Encoding]::ASCII.GetString((Invoke-WebRequest "http://download2.mikrotik.com/routeros/LATEST.6").Content)'
rmdir /s /q packer_cache && packer build -var "ros_ver=6.44.2" -var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json -on-error=ask -force routeros.json
```

## Notes
```shell
vagrant box add -f mt-test ./build/boxes/routeros.box
```

```ruby
Vagrant.configure("2") do |config|
  config.vm.box = "cheretbe/routeros"
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