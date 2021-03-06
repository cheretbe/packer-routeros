def quoted_string_to_mac_address(str)
  # "0800278917AB" ==> 08:00:27:89:17:AB
  return (str[1..2] + ":" + str[3..4] + ":" + str[5..6] +
    ":" + str[7..8] + ":" + str[9..10] + ":" + str[11..12])
end

def init_mac_address_list(machine)
  vm_nic_count = 0
  vm_NIC_mac_addresses = []

  vm_info = Hash.new
  machine.provider.driver.execute("showvminfo", machine.id, "--machinereadable").split("\n").each do |info_line|
    info_name, info_value = info_line.split("=", 2)
    vm_info[info_name] = info_value

    # showvminfo returns "none" for non-present network adapters
    # So we are dealing with values like these:
    # nic1="nat" nic2="hostonly" nic3="none" etc.
    if info_name.start_with?("nic") then
      if info_name.delete("nic").to_i != 0 and info_value != "\"none\"" then
        vm_nic_count += 1
      end
    end
  end

  # MAC addresses have format: macaddress1="0800278917AB" etc.
  # Convert them to "08:00:27:89:17:AB" format
  for i in 1..vm_nic_count
    vm_NIC_mac_addresses += [quoted_string_to_mac_address(vm_info["macaddress#{i}"])]
  end

  return vm_NIC_mac_addresses
end

module VagrantPlugins
  module GuestRouterOS
    class MacAddrSetup
      def initialize(app, env)
        @app = app
      end

      def call(env)
        @app.call(env)
        machine = env[:machine]
        if machine.config.vm.guest.to_s == "routeros"
          vm_NIC_mac_addresses = init_mac_address_list(machine)
          vm_nic_count = vm_NIC_mac_addresses.length
          machine.ui.detail("NIC MAC addresses: #{vm_NIC_mac_addresses}")
          machine.ui.detail("Uploading MAC address init script as 'vagrant_provision_mac_addr.rsc'")

          temp_file = Tempfile.new("vagrant-routeros")
          begin
            temp_file.write(":put \"Initializing global MAC address list\"\r\n")
            temp_file.write(":global vmNICMACs [:toarray \"" + vm_NIC_mac_addresses.join(", ") + "\"]\r\n")
            temp_file.write(":global vmNICCount #{vm_nic_count}\r\n")
            temp_file.close
            machine.communicate.upload(temp_file.path, "vagrant_provision_mac_addr.rsc")
          ensure
            temp_file.close
            temp_file.unlink
          end
        end
      end
    end #class MacAddrSetup
  end #module RouterOSInit
end #module VagrantPlugins
