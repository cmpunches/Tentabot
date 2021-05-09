import socket
import time
from .IRC_Event import *

class ConnectionContext:
    def __init__( self, server, port, nick, realname, nickserv_pass=None ):
        self.server = server
        self.port = port
        self.nick = nick
        self.realname = realname
        self.nickserv_pass = nickserv_pass


class IRC_Client:
    def __init__( self, context, suppress_events=[] ):
        self.server_details = context

        self.client = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
        # Connect to the server
        self.client.connect( ( context.server, context.port ) )

        self.suppress_events = suppress_events

        time.sleep(5)

        self.set_user()
        self.set_nick( context.nick )

    def set_user( self ):
        self.send_raw_quote(
            "USER {0} HOSTNAME * /{1} :{2}\n".format(
                self.server_details.nick,
                self.server_details.nick,
                self.server_details.nick,
                self.server_details.realname
            )
        )

    def set_nick( self, nick ):
        self.send_raw_quote( "NICK {0}\n".format( nick ) )

    def identify( self, nickserv_pass=None ):
        if nickserv_pass is not None:
            self.send_raw_quote(
                "NICKSERV IDENTIFY {0} {1}\n".format(
                    self.server_details.nick,
                    self.server_details.nickserv_pass
                )
            )

    def speak_in_channel( self, channel, msg ):
        self.send_raw_quote( "PRIVMSG {0} {1}\n".format( channel, msg ) )

    def join_channel( self, channel ):
        # join the channel
        self.send_raw_quote( "JOIN {0}\n".format( channel ) )

    def ping_respond( self, event ):
        raw_message = 'PONG ' + event.sender.host + '\r\n'
        self.send_raw_quote( raw_message )
        print( IRC_Event( 'PONG ' + event.sender.host + '\r\n' ) )

    def delimit_buffer(self, buffer ):
        tmp = buffer.split("\r\n")
        while ( "" in tmp ):
            tmp.remove("")
        return tmp

    def send_raw_quote( self, raw ):
        self.client.send( bytes( raw, "UTF-8" ) )

    def get_buffer(self):
        time.sleep(1)
        # Get the raw message response and return it
        resp = self.client.recv(8192).decode("UTF-8")
        return resp

    # hook to do more formatting
    def print_event(self, event ):
        print( event )

    def handle_disconnect(self):
        self.client.close()
        exit(1)

    # will be called in every iteration of the main loop
    # processes event from that loop
    # assumes a user event unless it's a server_message
    def process_event( self, event ):

        # give the user a print event
        if event.type not in self.suppress_events:
            self.print_event( event.as_json() )

        if event.type == EventType.SERVER_PING:
            self.ping_respond( event )

        if event.type == EventType.SERVER_ERROR:
            self.handle_disconnect()

    def run(self):
        # connection loop
        while True:
            # grab whatever is in the socket into buffer
            buffer = self.get_buffer()

            # delimit the buffer by carriage return, newline to represent raw IRC events
            raw_events = self.delimit_buffer(buffer)

            # iterate through raw events
            for raw_event in raw_events:
                # deserialize into a python object representing that event
                event = IRC_Event( raw_event )

                # for unknowns, print the representation
                if event.type == EventType.UNKNOWN:
                    print( raw_event )

                # otherwise process
                self.process_event(event)
