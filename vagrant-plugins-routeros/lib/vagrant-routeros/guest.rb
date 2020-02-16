module VagrantPlugins
  module GuestRouterOS
    class Guest < Vagrant.plugin("2", :guest)
      def detect?(machine)
        # Strictly speaking, detect? should never be called since we
        # set config.vm.guest to 'routeros' explicitly
        machine.config.vm.guest == "cheretbe/routeros"
      end
    end
  end
end