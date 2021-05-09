import datetime
import json
from enum import Enum, auto


class SenderType(Enum):
    SYSTEM = auto()
    USER = auto()
    LOCAL = auto()
    UNKNOWN = auto()


class Sender:
    def __init__( self, sender_string, stype=SenderType.UNKNOWN ):

        self.type = stype
        self.nick = None
        self.realname = None
        self.host = None

        if stype == SenderType.USER:
            tokenized = sender_string.replace('!', '|').replace('@', '|')
            fields = tokenized.split('|')
            self.nick = fields[0]
            self.realname = fields[1]
            self.host = fields[2]
        else:
            self.host = sender_string




    def as_dict(self):
        return {
                   'nick': self.nick,
                   'realname': self.realname,
                    'host': self.host,
                    'type': self.type.name
        }

    def as_json(self):
        return json.dumps( self.as_dict(), indent=4 )

    def __str__(self):
        return self.as_json()


# events we handle
class EventType(Enum):
    MOTD = auto()
    SERVER_PING = auto()
    CLIENT_PING = auto()
    CLIENT_PONG = auto()
    NOTICE = auto()
    CHANNEL_JOIN = auto()
    USER_MODE_CHANGE = auto()
    USER_MESSAGE = auto()
    RCV_PRIVATE_MESSAGE = auto()
    TOPIC = auto()
    SERVER_ERROR = auto()
    KICK = auto()
    # 474
    BANNED = 474
    # 473
    INVITE_ONLY = 473
    # 471
    CHANNEL_LIMIT = 471
    # 405
    TOO_MANY_CHANNELS = 405
    # unhandled event type
    UNKNOWN = auto()


# deserializes a raw event into a python object
class IRC_Event:
    def __init__( self, raw_message ):
        self.timestamp = '{:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now())
        self._raw_message = raw_message
        self.type = EventType.UNKNOWN
        self.sender = Sender( "Unknown", SenderType.UNKNOWN )
        self.message = None
        self.channel = None

        splat = raw_message.split(':')

        # Server messages
        if splat[0].startswith('PING'):
            self.type = EventType.SERVER_PING
            self.sender = Sender( splat[1], SenderType.SYSTEM )
            self.message = None
            self.channel = None
            return

        if splat[0].startswith('ERROR'):
            self.type = EventType.SERVER_ERROR
            self.sender = Sender( None, SenderType.SYSTEM )
            self.message = " ".join( raw_message.split(':')[1:] )
            self.channel = None
            return

        # client actions
        if splat[0].startswith('PONG'):
            self.type = EventType.CLIENT_PONG
            # embed this in the IRC server class so that you can replace known values
            self.sender = Sender( raw_message, SenderType.LOCAL )
            self.message = None
            self.channel = splat[0].split(' ')[1]
            return

        # user messages
        splonk = splat[1].split(' ')
        verb = splonk[1]
        sender = splonk[0]

        if verb == 'NOTICE':
            self.type = EventType.NOTICE
            self.sender = Sender( sender, SenderType.SYSTEM )
            self.message = splat[2]
            self.channel = sender
            return

        if verb == 'JOIN':
            self.type = EventType.CHANNEL_JOIN
            self.sender = Sender( sender, SenderType.USER )
            self.message = None
            self.channel = splat[2]
            return

        if verb == 'KICK':
            self.type = EventType.KICK
            self.sender = Sender( sender, SenderType.USER )
            self.message = None
            self.channel = splat[2]
            return

        if verb == 'MODE':
            self.type = EventType.USER_MODE_CHANGE
            self.sender = Sender( sender, SenderType.SYSTEM )
            self.message = splat[-1]
            self.channel = None
            return

        if verb.isdigit():
            self.type = EventType.MOTD
            self.sender = Sender( sender, SenderType.SYSTEM )
            # ':{sender} {verb} {nick} :{message}'
            self.message = " ".join( raw_message.split(" ")[3:] )[1:]
            self.channel = sender

            if int(verb) in (
                    int("001"),
                    int("002"),
                    int("003"),
                    int("004"),
                    int("005"),
                    251,
                    252,
                    253,
                    254,
                    255,
                    265,
                    266,
                    372,
                    375
            ):
                self.type = EventType.MOTD
            if int(verb) == EventType.BANNED:
                self.type = EventType.BANNED
            if int(verb) == EventType.INVITE_ONLY:
                self.type = EventType.INVITE_ONLY

            return

        if verb == 'PRIVMSG':
            self.type = EventType.USER_MESSAGE
            self.sender = Sender( sender, SenderType.USER )
            self.message = splat[2]
            self.channel = splonk[2]

            if not self.channel.startswith('#'):
                self.type = EventType.RCV_PRIVATE_MESSAGE
            return

        if verb == 'TOPIC':
            self.type = EventType.TOPIC
            self.sender = Sender( sender, SenderType.USER )
            self.message = splat[2]
            self.channel = splonk[2]
            return

    def as_dict(self):
        return {
                   'type': self.type.name,
                   'sender': self.sender.as_dict(),
                    'message': self.message,
                    'timestamp': self.timestamp,
                    'channel': self.channel,
                    '_raw_message': self._raw_message
        }

    def as_json(self):
        return json.dumps( self.as_dict(), indent=4 )

    def __str__(self):
        return self.as_json()