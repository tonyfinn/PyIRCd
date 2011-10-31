# Comments refer to variables in below strings.

class NumericReply:
    def __init__(self, number, message, final_multi=False):
        self.number = number
        self.num_str = str(self.number).zfill(3)
        self.message = message
        self.final_multi = final_multi

# nick!user@host
RPL_WELCOME = NumericReply(1, "Welcome to the Internet Relay Network {}!{}@{}")

# servername, version
RPL_YOURHOST = NumericReply(2, "Your host is {}, running version {}")

# Launch time
RPL_CREATED = NumericReply(3, "The server was created {}")

# servername, version, usermodes, channelmodes
RPL_MYINFO = NumericReply(4, "{} {} {} {}")

# Network name
RPL_ISUPPORT = NumericReply(5, "PREFIX=(ov)@+ CHANTYPES=#& NETWORK={}"
" CASEMAPPING=ascii :are supported by this server", True)

# Modes
RPL_UMODEIS = NumericReply(221, "+{}")

# nick, user, host, realname
RPL_WHOISUSER = NumericReply(311, "{} {} {} * :{}", True)

# nick, server host, server info
RPL_WHOISSERVER = NumericReply(312, "{} {} :{}", True)

# nick, time idle
RPL_WHOISIDLE = NumericReply(317, "{} {} :seconds idle", True)

# nick
RPL_ENDOFWHOIS = NumericReply(318, "{} :End of WHOIS list", True)

# nick, space seperated channel list
RPL_WHOISCHANNELS = NumericReply(319, "{} :{}", True)

# Channel, modes
RPL_CHANNELMODEIS = NumericReply(324, "{} +{}")

# Channel name
RPL_NOTOPIC = NumericReply(331, "{} :No topic is set", True)

# Channel name, topic
RPL_TOPIC = NumericReply(332, "{} :{}", True)

# Channel, user, host, server, nick, H is for here/gone, realname
RPL_WHOREPLY = NumericReply(352, "{} {} {} {} {} H{} :0 {}", True)

# WHO target
RPL_ENDOFWHO = NumericReply(315, "{} :End of WHO List", True)

# Channel name, space seperate list of nicks
RPL_NAMREPLY = NumericReply(353, "= {} :{}", True)

# Channel name
RPL_ENDOFNAMES = NumericReply(366, "{} :End of NAMES List", True)

# Server Name
RPL_MOTDSTART = NumericReply(375, ":- {} Message of the day - ", True)

# MOTD Component
RPL_MOTD = NumericReply(372, ":- {}", True)

RPL_ENDOFMOTD = NumericReply(376, ":End of MOTD", True)

# Nick
ERR_NOSUCHNICK = NumericReply(401, "{} :No such nick/channel", True)

# Channel name
ERR_NOSUCHCHANNEL = NumericReply(403, "{} :No such channel", True)

# Command attempted
ERR_NEEDMOREPARAMS = NumericReply(461, "{} :Not enough parameters", True)

# Nick
ERR_NICKNAMEINUSE = NumericReply(433, "{} :Nickname already in use", True)

# Channel
ERR_CHANOPRIVSNEEDED = NumericReply(
    482, "{} :You're not channel operator", True)

ERR_USERSDONTMATCH = NumericReply(
    502, ":Cannot change mode for other users", True)
