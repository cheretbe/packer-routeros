:global vmNICMACs

:local intnetMACaddr [:pick $vmNICMACs 2]
:if ([/interface ethernet get [find mac-address="$intnetMACaddr"] name] != "intnet") do={
  :put "Setting '$intnetMACaddr' interface name to 'intnet'"
  /interface ethernet set [find mac-address="$intnetMACaddr"] name="intnet"
}

:if ([:len [/ip address find interface="intnet" and address="192.168.199.12/24"]] = 0) do={
  :put "Adding IP 192.168.199.12/24 on interface 'intnet'"
  /ip address add address=192.168.199.12/24 interface="intnet"
}
