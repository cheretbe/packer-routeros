
variable "box_file_name" {
  type    = string
  default = "build/boxes/routeros.box"
}

variable "ros_ver" {
  type    = string
  default = ""
}

variable "vagrant_routeros_plugin_version" {
  type    = string
  default = ""
}

locals {
  ver_major = split(".", var.ros_ver)[0]
  ver_minor = split(".", var.ros_ver)[1]
  # 6.x: a - select all, i - install, n - do you want to keep old conf, y - disk erasure warning
  # 7.x: a - select all, i - install, y - disk erasure warning
  install_seq = local.ver_major >= 7 ? "a<wait>i<wait>y" : "a<wait>i<wait>n<wait>y"
  old_login_seq = "/user set [/user find name=\"admin\"] password=\"vagrant\"<enter>"
  v6_49_plus_login_seq = "vagrant<enter><wait><wait>vagrant<enter>"
  login_seq = local.ver_major >= 7 || (local.ver_major >= 6 && local.ver_minor >= 49) ? local.v6_49_plus_login_seq : local.old_login_seq
}

source "virtualbox-iso" "routeros" {
  boot_command            = [
    "<wait5>",
    local.install_seq,
    "<wait10><wait10><enter>",
    "<wait10><wait10><wait10>",
    "admin<enter><wait><wait>",
    "<enter><wait><wait>",
    "n<wait><wait>",
    "<enter><wait5>",
    local.login_seq,
    "<wait><wait>",
   "/ip dhcp-client add disabled=no interface=ether1 add-default-route=no use-peer-dns=no use-peer-ntp=no<enter>",
    "<wait5>",
    ":global packerHost \"http://{{ .HTTPIP }}:{{ .HTTPPort }}\"<enter>",
    "/tool fetch url=\"$packerHost/setup.rsc\" keep-result=yes dst-path=\"setup.rsc\"<enter>",
    "<wait5>", "/import setup.rsc<enter>",
    "<wait10><wait10><wait10>"
  ]
  headless                = true
  disk_size               = "256"
  format                  = "ova"
  guest_additions_mode    = "disable"
  guest_os_type           = "Linux_64"
  http_directory          = "."
  iso_checksum            = "none"
  iso_url                 = "https://download.mikrotik.com/routeros/${var.ros_ver}/mikrotik-${var.ros_ver}.iso"
  shutdown_command        = "execute \"/system shutdown\""
  ssh_password            = "vagrant"
  ssh_username            = "admin"
  ssh_wait_timeout        = "60s"
  vboxmanage              = [
    ["modifyvm", "{{ .Name }}", "--memory", "128"],
    ["modifyvm", "{{ .Name }}", "--graphicscontroller", "vmsvga"],
    ["modifyvm", "{{ .Name }}", "--vram", "128"],
    ["modifyvm", "{{ .Name }}", "--acpi", "on"],
    ["modifyvm", "{{ .Name }}", "--ioapic", "on"],
    ["modifyvm", "{{ .Name }}", "--hpet", "on"],
    ["modifyvm", "{{ .Name }}", "--rtcuseutc", "on"],
    ["modifyvm", "{{ .Name }}", "--pae", "on"],
    ["modifyvm", "{{ .Name }}", "--usb", "on"],
    ["modifyvm", "{{ .Name }}", "--usbehci", "off"]
  ]
  virtualbox_version_file = ""
  vm_name                 = "routeros"
}

build {
  sources = ["source.virtualbox-iso.routeros"]

  post-processor "vagrant" {
    keep_input_artifact  = false
    compression_level    = 9
    include              = [
      "vagrant-plugins-routeros/pkg/vagrant-routeros-${var.vagrant_routeros_plugin_version}.gem",
      "vagrant-plugins-routeros/vagrant_routeros_plugin_version.json"
    ]
    output               = "${var.box_file_name}"
    vagrantfile_template = "vagrantfile.template"
  }
}
