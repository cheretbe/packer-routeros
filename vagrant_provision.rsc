:put "Importing 'vagrant_provision_mac_addr.rsc'"
/import vagrant_provision_mac_addr.rsc

:global vmNICCount
:global vmNICMACs
:local hostNatMACaddr [:pick $vmNICMACs 0]
:local hostOnlyMACaddr [:pick $vmNICMACs 1]

:local continue ([:len [/interface ethernet find]] != $vmNICCount)
:local counter 0
:while ($continue) do={
  :put "Waiting for all interfaces to become available..."
  :delay 5
  :set counter ($counter + 1)
  :set continue ([:len [/interface ethernet find]] != $vmNICCount)
  :if ($counter=5) do={:set continue false}
}

:if ([/interface ethernet get [find mac-address="$hostNatMACaddr"] name] != "host_nat") do={
  :put "Setting '$hostNatMACaddr' interface name to 'host_nat'"
  /interface ethernet set [find mac-address="$hostNatMACaddr"] name="host_nat"
}

:if ([/interface ethernet get [find mac-address="$hostOnlyMACaddr"] name] != "host_only") do={
  :put "Setting '$hostOnlyMACaddr' interface name to 'host_only'"
  /interface ethernet set [find mac-address="$hostOnlyMACaddr"] name="host_only"
}

:if ([:len [/ip dhcp-client find interface="host_only"]] = 0) do={
  :put "Enabling DHCP on 'host_only' interface"
  /ip dhcp-client add disabled=no interface="host_only" add-default-route=no use-peer-dns=no use-peer-ntp=no
}