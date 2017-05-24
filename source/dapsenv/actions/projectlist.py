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

import asyncio
import sys
import json
import websockets
from dapsenv.actions.action import Action
from dapsenv.exitcodes import (E_API_SERVER_CONN_FAILED, E_API_SERVER_CLOSED_CONNECTION,
                               E_API_SERVER_INVALID_DATA_SENT)
from dapsenv.logmanager import log
from datetime import datetime
from prettytable import PrettyTable
from socket import gaierror


class Projectlist(Action):
    def __init__(self):
        pass

    def execute(self, args):
        """@see Action.execute()
        """
        self._args = args
        self._ip = self._args["ip"]
        self._port = self._args["port"]
        self._error = 0

        asyncio.get_event_loop().run_until_complete(self.start_client())

        if self._error:
            sys.exit(self._error)

    @asyncio.coroutine
    def start_client(self):
        try:
            ws = yield from websockets.connect("ws://{}:{}/".format(self._ip, self._port))

            # retrieve project list
            yield from ws.send(json.dumps({"id": 3}))

            # fetch server message
            res = yield from ws.recv()
            try:
                res = json.loads(res)
                first = True

                for project, dc_files in res["projects"].items():
                    if not first:
                        print("\n")

                    first = False
                    print("{}:".format(project))

                    for dc_file in dc_files:
                        print("\t{}".format(dc_file))
            except ValueError:
                log.error("Invalid data received from API server.")
                self._error = E_API_SERVER_INVALID_DATA_SENT
        except (ConnectionRefusedError, gaierror, OSError) as e:
            if "Connect call failed" in e.strerror or "Name or service not known" in e.strerror:
                log.error("Connection to API server failed. Check if the IP address and the "
                          "port are correct and if the firewall port is open.")
                self._error = E_API_SERVER_CONN_FAILED
        except websockets.exceptions.ConnectionClosed:
            log.error("The API server has closed the connection.")
            self._error = E_API_SERVER_CLOSED_CONNECTION
