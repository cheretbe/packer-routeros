Mikrotik RouterOS (https://mikrotik.com)

```shell
cd tools/vagrant-plugin-builder
vagrant up && vagrant ssh
cd /mnt/packer-mikrotik/vagrant-plugins-routeros/
bundle install; bundle exec rake build
```

```shell
# Linux
curl http://upgrade.mikrotik.com/routeros/LATEST.6
# long-term
curl http://upgrade.mikrotik.com/routeros/LATEST.6fix

rm packer_cache -rf; packer build -var 'ros_ver=6.46.3' \
  -var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json \
  -on-error=ask -force routeros.json

# Windows
powershell '[System.Text.Encoding]::ASCII.GetString((Invoke-WebRequest "http://download2.mikrotik.com/routeros/LATEST.6").Content)'
rmdir /s /q packer_cache && packer build -var "ros_ver=6.44.2" -var-file vagrant-plugins-routeros/vagrant_routeros_plugin_version.json -on-error=ask -force routeros.json

vagrant box add -f mt-test ./build/boxes/routeros.box

vagrant plugin install vagrant-triggers
```

```shell
vagrant cloud box show cheretbe/routeros
curl -sS https://app.vagrantup.com/api/v1/box/cheretbe/routeros | jq -r ".current_version.version"

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

```
system "vagrant ssh #{machine.name} -- :global aaa [:toarray \"aaa1, aaa2, aaa3\"]"
```
