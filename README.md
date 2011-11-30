This is an IRC server written in Python. At the moment, it supports 
a lot of the client protocol as specified in RFC 2812, but no server to
server features.

Supported Features
===

* Channels
* Messaging (channels and PMs)
* WHOIS, NAMES, WHO
* Message of the Day
* Changing topics
* Channel modes (voice, op, limits, keys etc.)
* Opers

Todo
===

* Add server linking features. This will likely mean splitting IRCNet into
  two classes - one to handle specific server things and one to handle
  communicating with the rest of the network.
* Actually pay attention to some extra modes like m or s.
