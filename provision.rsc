:if ([/interface ethernet get [find default-name="ether1"] name] != "host_nat") do={
  :put "Setting 'ether1' interface name to 'host_nat'"
  /interface ethernet set [find default-name="ether1"] name="host_nat"
}

:local continue ([:len [/interface ethernet find default-name="ether2"]] = 0)
:local counter 0
:while ($continue) do={
  :put "Waiting for 'ether2' interface to become available..."
  :delay 5
  :set counter ($counter + 1)
  :set continue ([:len [/interface ethernet find default-name="ether2"]] = 0)
  :if ($counter=5) do={:set continue false}
}

:if ([/interface ethernet get [find default-name="ether2"] name] != "host_only") do={
  :put "Setting 'ether2' interface name to 'host_only'"
  /interface ethernet set [find default-name="ether2"] name="host_only"
}

/interface ethernet reset-mac-address "host_only"

:if ([:len [/ip dhcp-client find interface="host_only"]] = 0) do={
  :put "Enabling DHCP on 'host_only' interface"
  /ip dhcp-client add disabled=no interface="host_only" add-default-route=no use-peer-dns=no use-peer-ntp=no
}