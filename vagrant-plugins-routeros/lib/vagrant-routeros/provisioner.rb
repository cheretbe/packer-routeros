require "open3"

def upload_ros_file(machine, source_file_path, target_file_path)
  machine.ui.detail("Uploading file '#{source_file_path}' as '#{target_file_path}'")
  machine.communicate.upload(source_file_path, target_file_path)
end

def run_ros_command(machine, ros_command, check_script_error: false)
  machine.ui.detail("Executing '#{ros_command}'")

  has_script_error = true
  # https://docs.ruby-lang.org/en/2.5.0/Open3.html
  Open3.popen2e("vagrant", "ssh", "#{machine.name}", "--", ros_command) do |stdin, stdout_stderr, status_thread|
    stdout_stderr.each_line do |line|
      machine.ui.detail(line.chomp)
      has_script_error = false if line.include?("Script file loaded and executed successfully")
    end
    raise "ROS command failed"  unless status_thread.value.success?
    raise "ROS command failed" if has_script_error and check_script_error
  end
end

module VagrantPlugins
  module GuestRouterOS

    class CommandProvisioner < Vagrant.plugin("2", "provisioner")
      def provision
        run_ros_command(@machine, @config.command)
      end
    end

    class CommandProvisionerConfig < Vagrant.plugin("2", "config")
      attr_accessor :command
      attr_accessor :name

      def initialize
        super
        @command     = UNSET_VALUE
        @name        = UNSET_VALUE
      end

      def finalize!
        @command     = nil if @command == UNSET_VALUE
        @name        = nil if @name == UNSET_VALUE
      end

      def validate(machine)
        errors = _detected_errors

        if !command
          errors << "`command` parameter must be set"
        end

        { "RouterOS command provisioner" => errors }
      end
    end

    class FileProvisioner < Vagrant.plugin("2", "provisioner")
      def provision
        upload_ros_file(@machine, @config.source, @config.destination)
      end
    end

    class FileProvisionerConfig < Vagrant.plugin("2", "config")
      attr_accessor :source
      attr_accessor :destination
      attr_accessor :name

      def initialize
        super
        @source      = UNSET_VALUE
        @destination = UNSET_VALUE
        @name        = UNSET_VALUE
      end

      def finalize!
        @source      = nil if @source == UNSET_VALUE
        @destination = nil if @destination == UNSET_VALUE
        @name        = nil if @name == UNSET_VALUE
      end

      def validate(machine)
        errors = _detected_errors

        if !source
          errors << "File source must be specified."
        end
        if !destination
          errors << "File destination must be specified."
        end
        if source
          s = Pathname.new(source).expand_path(machine.env.root_path)
          if !s.exist?
            errors << ("File upload source file %{path} must exist" % { path: s.to_s })
          end
        end

        { "RouterOS file provisioner" => errors }
      end
    end

  end
end
