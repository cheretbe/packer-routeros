Mikrotik RouterOS (https://mikrotik.com)

```
packer build -var 'ros_ver=6.40.6' -on-error=ask -force routeros.json

vagrant plugin install vagrant-triggers
```

```ruby
# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "mt-test"
  config.vm.provider "virtualbox" do |vb|
    vb.customize ["modifyvm", :id, "--groups", "/__vagrant"]
  end
  config.trigger.instead_of :halt do
    run "vagrant ssh -- \"/system shutdown\""
  end
end
```
