from pyircd.message import Message

# Comments refer to variables in below strings.

class NumericReply():
    def __init__(self, number, message, final_multi=True):
        self.number = number
        self.num_str = str(self.number).zfill(3)
        self.message = message
        self.final_multi = final_multi

# nick!user@host
RPL_WELCOME = NumericReply(
        1, 
        ":Welcome to the Internet Relay Network {}!{}@{}"
    )

# servername, version
RPL_YOURHOST = NumericReply(2, ":Your host is {}, running version {}")

# Launch time
RPL_CREATED = NumericReply(3, ":This server was created {}")

# servername, version, usermodes, channelmodes
RPL_MYINFO = NumericReply(4, "{} {} {} {}", False)

# Network name
RPL_ISUPPORT = NumericReply(5, "PREFIX=(ov)@+ CHANTYPES=#& NETWORK={}"
" CASEMAPPING=ascii CHANMODES=beI,k,l,imnst EXCEPTS=e CHANNELLEN=32"
":are supported by this server")

# Modes
RPL_UMODEIS = NumericReply(221, "+{}", False)

# nick, user, host, realname
RPL_WHOISUSER = NumericReply(311, "{} {} {} * :{}")

# nick, server host, server info
RPL_WHOISSERVER = NumericReply(312, "{} {} :{}")

# nick, time idle
RPL_WHOISIDLE = NumericReply(317, "{} {} :seconds idle")

# nick
RPL_ENDOFWHOIS = NumericReply(318, "{} :End of WHOIS list")

# nick, space seperated channel list
RPL_WHOISCHANNELS = NumericReply(319, "{} :{}")

# Channel, modes, mode params
RPL_CHANNELMODEIS = NumericReply(324, "{} +{} {}", False)

# Channel name
RPL_NOTOPIC = NumericReply(331, "{} :No topic is set")

# Channel name, topic
RPL_TOPIC = NumericReply(332, "{} :{}")

# Channel, user, host, server, nick, H is for here/gone, realname
RPL_WHOREPLY = NumericReply(352, "{} {} {} {} {} H{} :0 {}")

# WHO target
RPL_ENDOFWHO = NumericReply(315, "{} :End of WHO List")

# Channel name, space seperate list of nicks
RPL_NAMREPLY = NumericReply(353, "= {} :{}")

# Channel name
RPL_ENDOFNAMES = NumericReply(366, "{} :End of NAMES List")

# Server Name
RPL_MOTDSTART = NumericReply(375, ":- {} Message of the day - ")

# MOTD Component
RPL_MOTD = NumericReply(372, ":- {}")

RPL_ENDOFMOTD = NumericReply(376, ":End of MOTD")

RPL_YOUREOPER = NumericReply(381, ":You are now an IRC operator")

# Nick
ERR_NOSUCHNICK = NumericReply(401, "{} :No such nick/channel")

# Channel name
ERR_NOSUCHCHANNEL = NumericReply(403, "{} :No such channel")

# Failed command
ERR_UNKNOWNCOMMAND = NumericReply(421, "{} :Unknown command")

# Nick
ERR_NICKNAMEINUSE = NumericReply(433, "{} :Nickname already in use")

# Nick, channel
ERR_USERNOTINCHANNEL = NumericReply(441, "{} {} :They aren't on that channel")

# Channel
ERR_NOTONCHANNEL = NumericReply(442, "{}: You're not on that channel")

# Command attempted
ERR_NEEDMOREPARAMS = NumericReply(461, "{} :Not enough parameters")

ERR_PASSWDMISMATCH = NumericReply(464, ":Password incorrect")

# Channel
ERR_CHANNELISFULL = NumericReply(471, "{} :Cannot join channel (+l)")

# Channel
ERR_BADCHANNELKEY = NumericReply(475, "{} :Cannot join channel (+k)")

# Channel
ERR_BADCHANMASK = NumericReply(476, "{} :Bad Channel Mask")

# Channel
ERR_CHANOPRIVSNEEDED = NumericReply(482, "{} :You're not channel operator")

ERR_USERSDONTMATCH = NumericReply(502, ":Cannot change mode for other users")
