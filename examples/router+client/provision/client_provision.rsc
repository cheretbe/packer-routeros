:global vmNICMACs

:local lanMACaddr [:pick $vmNICMACs 2]
:if ([/interface ethernet get [find mac-address="$lanMACaddr"] name] != "lan") do={
  :put "Setting '$lanMACaddr' interface name to 'lan'"
  /interface ethernet set [find mac-address="$lanMACaddr"] name="lan"
}

:if ([:len [/ip address find interface="lan" and address="192.168.199.10/24"]] = 0) do={
  :put "Adding IP 192.168.199.10/24 on interface 'lan'"
  /ip address add address=192.168.199.10/24 interface="lan"
}

if ([/ip dns get servers] != "192.168.199.1") do={
  :put "Setting DNS server to 192.168.199.1"
  /ip dns set servers=192.168.199.1
}

:if ([:len [/ip route find gateway="192.168.199.1"]] = 0) do={
  :put "Adding default route via 192.168.199.1"
  /ip route add distance=1 gateway=192.168.199.1
}
