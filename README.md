Mikrotik RouterOS (https://mikrotik.com)

```
curl http://download2.mikrotik.com/routeros/LATEST.6
packer build -var 'ros_ver=6.41.3' -on-error=ask -force routeros.json

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
