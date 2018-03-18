/interface ethernet
set [ find default-name=ether1 ] name=host_nat

:global packerHost
:put "Fetching $packerHost/vagrant_insecure.key"
/tool fetch url="$packerHost/vagrant_insecure.key" keep-result=yes dst-path="vagrant.key"
:delay 5

:put "Adding 'vagrant' user"
/user add name=vagrant password=vagrant group=full
/user ssh-keys import user=vagrant public-key-file=vagrant.key

# https://wiki.mikrotik.com/wiki/Manual:System/Packages
:put "Disabling packages"
/system package disable calea,dude,gps,ipv6,kvm,lcd,ups

:put "Fetching $packerHost/provision.rsc"
/tool fetch url="$packerHost/provision.rsc" keep-result=yes dst-path="provision.rsc"
:delay 5
:put "Adding 'provision' script"
/system script add name=provision source=[/file get provision.rsc contents]
:delay 5
/file remove provision.rsc

:put "Fetching $packerHost/enable_smb.rsc"
/tool fetch url="$packerHost/enable_smb.rsc" keep-result=yes dst-path="enable_smb.rsc"
:delay 5
:put "Adding 'enable_smb' script"
/system script add name=enable_smb source=[/file get enable_smb.rsc contents]
:delay 5
/file remove enable_smb.rsc

/file remove setup.rsc