module VagrantPlugins
  module GuestRouterOS
    module Cap
      class Halt
        def self.halt(machine)
          begin
            machine.ui.detail("Executing '/system shutdown' command")
            # system ("vagrant ssh #{machine.name} -- ':execute \{ :delay 10; /system shutdown \}'")
            system ("vagrant ssh #{machine.name} -- '/system shutdown'")
          rescue IOError => e
            # TODO: Consider using @logger.warn(e)
            machine.ui.warn(e)
            # Ignore, this probably means connection closed because it
            # shut down.
          end
        end
      end
    end
  end
end