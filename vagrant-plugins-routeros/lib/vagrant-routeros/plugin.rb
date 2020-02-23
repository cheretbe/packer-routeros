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

      guest_capability('routeros', 'change_host_name') do
        require_relative 'cap/change_host_name'
        Cap::ChangeHostName
      end

      provisioner "routeros_command" do
        require_relative "provisioner"
        CommandProvisioner
      end

      config("routeros_command", :provisioner) do
        require_relative "provisioner"
        CommandProvisionerConfig
      end

      provisioner "routeros_file" do
        require_relative "provisioner"
        FileProvisioner
      end

      config("routeros_file", :provisioner) do
        require_relative "provisioner"
        FileProvisionerConfig
      end

      action_hook "router_os_mac_addr_setup" do |hook|
        require_relative "mac_addr_setup"
        # hook.before Vagrant::Action::Builtin::Provision, MacAddrSetup
        hook.after Vagrant::Action::Builtin::WaitForCommunicator, MacAddrSetup
      end
    end
  end
end