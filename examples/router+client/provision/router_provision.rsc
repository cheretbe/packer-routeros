:global vmNICMACs

:local lanMACaddr [:pick $vmNICMACs 2]

:local natUseDNS [/ip dhcp-client get [find interface="host_nat"] use-peer-dns]
:local natAddRoute [/ip dhcp-client get [find interface="host_nat"] add-default-route]
if (!$natUseDNS or ($natAddRoute != "yes")) do={
  :put "Using DHCP-assigned DNS server and default route on 'host_nat' interface"
  /ip dhcp-client set [find interface="host_nat"] use-peer-dns=yes add-default-route=yes
}

:if ([/interface ethernet get [find mac-address="$lanMACaddr"] name] != "lan") do={
  :put "Setting '$lanMACaddr' interface name to 'lan'"
  /interface ethernet set [find mac-address="$lanMACaddr"] name="lan"
}

:if ([:len [/ip address find interface="lan" and address="192.168.199.1/24"]] = 0) do={
  :put "Adding IP 192.168.199.1/24 on interface 'lan'"
  /ip address add address=192.168.199.1/24 interface="lan"
}

if ([:len [/interface list find name="WAN"]] = 0) do={
  :put "Adding 'WAN' interface list"
  /interface list add name=WAN comment="defconf"
}
if ([:len [/interface list member find list="WAN" and interface="host_nat"]] = 0) do={
  :put "Adding 'host_nat' interface to 'WAN' interface list"
  /interface list member add list=WAN interface=host_nat comment="defconf"
}
if ([:len [/interface list find name="LAN"]] = 0) do={
  :put "Adding 'LAN' interface list"
  /interface list add name=LAN comment="defconf"
}
if ([:len [/interface list member find list="LAN" and interface="lan"]] = 0) do={
  :put "Adding 'lan' interface to 'LAN' interface list"
  /interface list member add list=LAN interface=lan comment="defconf"
}
if ([:len [/interface list find name="ALLOW_DISCOVERY"]] = 0) do={
  :put "Adding 'ALLOW_DISCOVERY' interface list"
  /interface list add name=ALLOW_DISCOVERY comment="defconf"
}
if ([:len [/interface list member find list="ALLOW_DISCOVERY" and interface="lan"]] = 0) do={
  :put "Adding 'lan' interface to 'ALLOW_DISCOVERY' interface list"
  /interface list member add list=ALLOW_DISCOVERY interface=lan comment="defconf"
}
if ([:len [/interface list member find list="ALLOW_DISCOVERY" and interface="host_only"]] = 0) do={
  :put "Adding 'host_only' interface to 'ALLOW_DISCOVERY' interface list"
  /interface list member add list=ALLOW_DISCOVERY interface=host_only comment="defconf"
}

if (![/ip dns get allow-remote-requests]) do={
  :put "Enabling DNS server"
  /ip dns set allow-remote-requests=yes
}

if ([:len [/ip firewall filter find]] = 0) do={
  :put "Adding firewall rules"
  /ip firewall {
    filter add chain=input action=accept connection-state=established,related,untracked comment="defconf: accept established,related,untracked"
    filter add chain=input action=drop connection-state=invalid comment="defconf: drop invalid"
    filter add chain=input action=accept protocol=icmp comment="defconf: accept ICMP"
    filter add chain=input action=accept dst-port=22 in-interface=host_nat protocol=tcp comment="defconf: accept SSH connections from Vagrant"
    filter add chain=input action=accept dst-port=8291 in-interface=host_only protocol=tcp comment="defconf: accept Winbox connections from host-only interface"
    filter add chain=input action=drop in-interface-list=!LAN comment="defconf: drop all not coming from LAN"
    filter add chain=forward action=accept ipsec-policy=in,ipsec comment="defconf: accept in ipsec policy"
    filter add chain=forward action=accept ipsec-policy=out,ipsec comment="defconf: accept out ipsec policy"
    filter add chain=forward action=fasttrack-connection connection-state=established,related comment="defconf: fasttrack"
    filter add chain=forward action=accept connection-state=established,related,untracked comment="defconf: accept established,related, untracked"
    filter add chain=forward action=drop connection-state=invalid comment="defconf: drop invalid"
    filter add chain=forward action=drop connection-state=new connection-nat-state=!dstnat in-interface-list=WAN comment="defconf: drop all from WAN not DSTNATed"
  }
}

if ([:len [/ip firewall nat find chain="srcnat" and out-interface-list="WAN" and action="masquerade"]] = 0) do={
  :put "Adding masquerade rule"
  /ip firewall nat add chain=srcnat out-interface-list=WAN ipsec-policy=out,none action=masquerade comment="defconf: masquerade"
}

if ([/ip neighbor discovery-settings get discover-interface-list] != "ALLOW_DISCOVERY") do={
  :put "Allowing neighbour discovery on 'ALLOW_DISCOVERY' interface list"
  /ip neighbor discovery-settings set discover-interface-list=ALLOW_DISCOVERY
}
if ([/tool mac-server get allowed-interface-list] != "LAN") do={
  :put "Allowing MAC Telnet Server on 'LAN' interface list"
  /tool mac-server set allowed-interface-list=LAN
}
if ([/tool mac-server mac-winbox get allowed-interface-list] != "LAN") do={
  :put "Allowing MAC WinBox Server on 'LAN' interface list"
  /tool mac-server mac-winbox set allowed-interface-list=LAN
}
