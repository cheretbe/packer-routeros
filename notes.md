* https://www.vagrantup.com/docs/plugins/guests.html
* https://www.vagrantup.com/docs/plugins/guest-capabilities.html
* https://github.com/hashicorp/vagrant/blob/master/plugins/guests/windows/plugin.rb
* search pattern `filename:Vagrantfile guest require_relative Vagrant.plugin`
* https://github.com/bensallen/rancheros-box/blob/master/vagrant_rancheros_guest_plugin.rb


```ruby
  config.trigger.after :up, :provision, :reload, :resume do |trigger|
    trigger.ruby do |env,machine|
      trigger.name = "Init MAC address list"
      if !machine.respond_to?(:vm_nic_count) then
        init_mac_address_list(machine)
        # [!] vm_NIC_mac_addresses array is 0-based
        system "vagrant ssh #{machine.name} -- ':global vmNICMACs [:toarray \"" +
          machine.vm_NIC_mac_addresses.join(", ") + "\"]'"
        system "vagrant ssh #{machine.name} -- ':global vmNICCount #{machine.vm_nic_count}'"
        system "vagrant ssh #{machine.name} -- /system script run provision"
      end
      puts "!!!!!!!!!!!!!!!!!!!!"
      machine.define_singleton_method :test do |name|
        puts "there you go #{name}"
        puts "self.name: #{self.name}"
      end
    end
  end
```
-------
```ruby
def handle_comm(machine, type, data)
  if [:stderr, :stdout].include?(type)
    # Output the data with the proper color based on the stream.
    color = type == :stdout ? :green : :red

    # Clear out the newline since we add one
    data = data.chomp
    return if data.empty?

    options = {}
    options[:color] = color if !config.keep_color

    machine.ui.detail(data.chomp, options)
  end
end
```
-------
```ruby
  config.trigger.after :up, :provision, :reload, :resume do |trigger|
    trigger.ruby do |env,machine|
      machine.test("aaa")
      machine.ui.detail("need to replace puts with this")
      machine.ui.detail("machine.custom_provision_enabled: #{machine.custom_provision_enabled}")
      # puts "machine.communicate.ready?: #{machine.communicate.ready?}"
      # machine.communicate.test("/system resource print")
      # binding.pry
      # machine.communicate.upload('Vagrantfile', 'test_file')
      upload_mikrotik_file(machine, "Vagrantfile", "test_file")
      # machine.communicate.execute("/system resource print", sudo: false)
      # machine.communicate.execute(
      #   "/system resource print",
      #   sudo: false,
      #   error_key: :ssh_bad_exit_status_muted,
      #   error_check: true
      # ) do |type, data|
      #   handle_comm(machine, type, data)
      # end


      # ssh_opts = {
      #   plain_mode: false,
      #   subprocess: false,
      #   extra_args: ["/system resource print"]
      # }
      # binding.pry
      # machine.action(:ssh_run, ssh_opts: ssh_opts, ssh_run_command: "", tty: true)
    end
  end
  ```
