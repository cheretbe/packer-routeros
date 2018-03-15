/interface ethernet
set [ find default-name=ether1 ] name=host_nat
set [ find default-name=ether2 ] name=host_only

/ip dhcp-client add disabled=no interface=host_only add-default-route=no use-peer-dns=no use-peer-ntp=no

/user add name=vagrant password=vagrant group=full
/user ssh-keys import user=vagrant public-key-file=vagrant.key