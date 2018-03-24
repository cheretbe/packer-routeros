Mikrotik RouterOS (https://mikrotik.com)

```shell
curl http://download2.mikrotik.com/routeros/LATEST.6
# Linux
rm packer_cache -rf; packer build -var 'ros_ver=6.41.3' -on-error=ask -force routeros.json
# Windows
rmdir /s /q packer_cache & packer build -var 'ros_ver=6.41.3' -on-error=ask -force routeros.json

vagrant box add -f mt-test ./build/boxes/routeros.box

vagrant plugin install vagrant-triggers
```

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "cheretbe/routeros"
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--groups", "/__vagrant"]
  end
end
```
