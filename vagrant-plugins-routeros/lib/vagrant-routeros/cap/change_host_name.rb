module VagrantPlugins
  module GuestRouterOS
    module Cap
      class ChangeHostName
        def self.change_host_name(machine, name)
          system("vagrant ssh #{machine.name} -- '" +
            ":if ([/system identity get name] != \"#{name}\") do={ /system identity set name=\"#{name}\" }'")
        end
      end
    end
  end
end