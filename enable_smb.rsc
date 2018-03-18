:if (![/ip smb get enabled]) do={
  :put "Enabling SMB"
  /ip smb set enabled=yes
}

:if ([:len [/ip smb user find name="vagrant"]] = 0) do={
  :put "Adding user 'vagrant'"
  /ip smb user add read-only=no name="vagrant" password="vagrant"
}

:if ([:len [/ip smb share find name="vagrant"]] = 0) do={
  :put "Adding 'vagrant' share"
  /ip smb share add name="vagrant" directory="/"
}