This is an IRC server written in Python. At the moment, it supports 
a lot of the client protocol as specified in RFC 2812, but no server to
server features.

=== Supported Features ===
* Channels
* Messaging (channels and PMs)
* WHOIS, NAMES, WHO
* Message of the Day

=== Known Issues ===
* Pidgin (and other libpurple clients) can not join channels - for some
  reason they send the user's nick as an extra parameter in JOIN
  commands.
