#
# Copyright (c) 2016 SUSE Linux GmbH
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of version 3 of the GNU General Public License as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact SUSE LLC.
#
# To contact SUSE about this file by physical or electronic mail,
# you may find current contact information at www.suse.com

import irc.bot
import irc.connection
import irc.schedule
import irc.strings
import ssl


class IRCBot(irc.bot.SingleServerIRCBot):

    def __init__(self, server, port, channel, nickname, username):
        """Initializes the IRC Bot class

        :param string server: The IP-Address/Hostname of the IRC server
        :param int port: Port of the IRC server
        :param string channel: The channel to join
        :param string nickname: Nickname of the bot on the IRC server
        :param string username: Username of the bot on the IRC server
        """

        irc.bot.SingleServerIRCBot.__init__(
            self, [(server, port)],
            nickname,
            username,
            connect_factory=irc.connection.Factory(wrapper=ssl.wrap_socket))

        self._channel = channel
        self._daemon = None

    def on_nicknameinuse(self, c, e):
        """Callback for Nickname-Issues

        :param irc.client.ServerConnectionserver c: Connection object
        :param irc.client.Event e: Client event object
        """

        self.disconnect("irc naming issue")

    def on_welcome(self, c, e):
        """Will be called after the bot has established a connection to the IRC server

        :param irc.client.ServerConnectionserver c: Connection object
        :param irc.client.Event e: Client event object
        """

        self.connection.buffer.errors = "replace"
        c.join(self._channel)

    def on_privmsg(self, c, e):
        """Callback for private messages - if a client sends a message to the bot

        :param irc.client.ServerConnectionserver c: Connection object
        :param irc.client.Event e: Client event object
        """

        # get sent text
        cmd = " ".join(e.arguments[0].split()[:1])
        args = e.arguments[0].split()[1:]

        # parse commands
        if cmd == "status":
            if not self._daemon:
                c.privmsg(e.source.nick, "Sorry, Daemon object is not yet initialized!")
                return

            status = self._daemon.getStatus()
            c.privmsg(e.source.nick, "Running Builds: {}, "
                                     "Scheduled Builds: {}".format(status["running_builds"],
                                                                   status["scheduled_builds"])
                      )

            active_builds = []
            for builds in status["jobs"]:
                active_builds.append(builds["dc_file"])

            if active_builds:
                c.privmsg(e.source.nick, "Active Builds: {}".format(", ".join(active_builds)))
        elif cmd == "buildinfo":
            if not args:
                c.privmsg(e.source.nick, "Syntax: buildinfo [DC-File]")
            else:
                status = self._daemon.getStatus()
                dc_file = args[0]

                for job in status["jobs"]:
                    if job["dc_file"] == dc_file:
                        started_info = "No"
                        container_id = "Unknown"

                        if job["status"]:
                            started_info = "Yes"

                            if job["container_id"]:
                                container_id = job["container_id"]

                        c.privmsg(e.source.nick, "Build started? {}, Container-ID: {}".format(
                            started_info,
                            container_id
                        ))

                        return

                c.privmsg(e.source.nick, "There is currently no build running with that DC-File.")
        elif cmd == "ping":
            c.privmsg(e.source.nick, "pong!")
        else:
            c.privmsg(e.source.nick, "Bad command! Available commands: status, ping, buildinfo")

    def sendChannelMessage(self, message):
        """Sends a message to the channel which the bot joined

        :param string message: The message to be sent
        """

        self.connection.privmsg(self._channel, message)

    def sendClientMessage(self, client, message):
        """Sends a message to a client

        :param string client: The name of the client
        :param string message: The message to be sent
        """

        self.connection.privmsg(client, message)

    def setDaemon(self, obj):
        """Sets the daemon object for the communication between the daemon and the bot

        :param Daemon obj: The Daemon class object
        """

        self._daemon = obj
