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
    RETAIN_FILE_ON_ERROR  = "on error".freeze
    RETAIN_FILE_YES       = "yes".freeze
    RETAIN_FILE_NO        = "no".freeze
    RETAIN_FILE_MODES         = [
      RETAIN_FILE_ON_ERROR,
      RETAIN_FILE_YES,
      RETAIN_FILE_NO,
    ].freeze

    class Provisioner < Vagrant.plugin("2", "provisioner")
      def provision
        if @config.inline then
          # @machine.ui.detail("Executing '#{@config.inline}'")
          run_ros_command(@machine, @config.inline)
        else
          upload_ros_file(@machine, @config.path, "CHANGE_ME.rsc")
          run_ros_command(@machine, "/import CHANGE_ME.rsc", check_script_error: true)
        end
      end
    end

    class ProvisionerConfig < Vagrant.plugin("2", "config")
      attr_accessor :inline
      attr_accessor :name
      attr_accessor :path
      attr_accessor :retain_file

      def initialize
        super
        @inline      = UNSET_VALUE
        @name        = UNSET_VALUE
        @path        = UNSET_VALUE
        @retain_file = RETAIN_FILE_ON_ERROR
      end

      def finalize!
        @inline      = nil if @inline == UNSET_VALUE
        @name        = nil if @name == UNSET_VALUE
        @path        = nil if @path == UNSET_VALUE
        @retain_file = nil unless RETAIN_FILE_MODES.include?(@retain_file)
      end

      def validate(machine)
        errors = _detected_errors

        if path && inline
          errors << "Only one of `path` or `inline` may be set"
        elsif !path && !inline
          errors << "One of `path` or `inline` must be set"
        end

        if !retain_file
          errors << "`retain_file` must be a valid mode (possible values: " +
            RETAIN_FILE_MODES.map { |s| "'#{s}'" }.join(', ') + ")"
        end

        { "routeros provisioner" => errors }
      end
    end
  end
end
