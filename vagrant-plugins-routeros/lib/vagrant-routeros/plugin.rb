require "vagrant"

module VagrantPlugins
  module GuestRouterOS
    class Plugin < Vagrant.plugin("2")
      name "RouterOS"
      description "Mikroitik RouterOS support"

      guest("routeros") do
        require_relative "guest"
        Guest
      end

      guest_capability("routeros", "halt") do
        require_relative "cap/halt"
        Cap::Halt
      end

      provisioner "routeros" do
        require_relative "provisioner"
        Provisioner
      end

      config("routeros", :provisioner) do
        require_relative "provisioner"
        ProvisionerConfig
      end
    end
  end
end