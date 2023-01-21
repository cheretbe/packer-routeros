:global packerHost

:put "Fetching $packerHost/vagrant_insecure.key => vagrant.key"
/tool fetch url="$packerHost/vagrant_insecure.key" keep-result=yes dst-path="vagrant.key"

:put "Fetching $packerHost/vagrant_provision.rsc => vagrant_provision.rsc"
/tool fetch url="$packerHost/vagrant_provision.rsc" keep-result=yes dst-path="vagrant_provision.rsc"

if ([:pick [/system package update get installed-version] 0 1] = "6") do={
  # https://wiki.mikrotik.com/wiki/Manual:System/Packages
  :local PkgSet "calea,dude,gps,ipv6,kvm,lcd,ups";
  :put "Disabling packages: $PkgSet"
  /system package disable $PkgSet
}

:put "Waiting 2s for RouterOS to make vagrant.key file available"
:delay 2

:put "Adding 'vagrant' user with vagrant.key SSH access"
/user add name=vagrant password=vagrant group=full
/user ssh-keys import user=vagrant public-key-file=vagrant.key

:put "Removing setup.rsc script"
/file remove setup.rsc
