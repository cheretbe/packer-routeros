/interface ethernet
set [ find default-name=ether1 ] name=host_nat

/user add name=vagrant password=vagrant group=full
/user ssh-keys import user=vagrant public-key-file=vagrant.key