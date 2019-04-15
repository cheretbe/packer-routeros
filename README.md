Mikrotik RouterOS (https://mikrotik.com)

```shell
# Linux
curl http://download2.mikrotik.com/routeros/LATEST.6
rm packer_cache -rf; packer build -var 'ros_ver=6.44.2' -on-error=ask -force routeros.json

# Windows
powershell '[System.Text.Encoding]::ASCII.GetString((Invoke-WebRequest "http://download2.mikrotik.com/routeros/LATEST.6").Content)'
rmdir /s /q packer_cache && packer build -var "ros_ver=6.44.2" -on-error=ask -force routeros.json

vagrant box add -f mt-test ./build/boxes/routeros.box

vagrant plugin install vagrant-triggers
```

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "cheretbe/routeros"
  # config.vm.box = "mt-test"
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--groups", "/__vagrant"]
  end
end
```

```
system "vagrant ssh #{machine.name} -- :global aaa [:toarray \"aaa1, aaa2, aaa3\"]"
```