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
import dapsenv.api.status as APIStatus
import dapsenv.api.triggerbuild as APITriggerBuild
import dapsenv.api.projectlist as APIProjectList
import dapsenv.api.viewlog as APIViewLog
import json
import threading
import websockets
from dapsenv.exceptions import (APIInvalidRequestException, APIUnauthorizedTokenException,
                                APIErrorException)


class APIServer:

    def __init__(self, ip, port, daemon):
        self._ip = ip
        self._port = port
        self._daemon = daemon

    def serve(self):
        thread = threading.Thread(target=self._serve)
        thread.start()

    def _serve(self):
        # set event loop handler
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # configure websocket server
        start_server = websockets.serve(self._api_server_runtime, self._ip, self._port)

        # event loop settings
        asyncio.get_event_loop().run_until_complete(start_server)
        asyncio.get_event_loop().run_forever()

    @asyncio.coroutine
    def _api_server_runtime(self, websocket, path):
        """This coroutine will be created for each new client what connects to the API server

        :param websockets.server.WebSocketServerProtocol websocket: Object for communicating with
                                                                    the current client
        :param string path: The path where the client want to go to
        """

        while True:
            try:
                # wait until the client sends data to the API server
                try:
                    data = yield from websocket.recv()
                except websockets.exceptions.ConnectionClosed:
                    return

                try:
                    # parse the sent data as json
                    data = json.loads(data)

                    # check for correct data packets
                    if "id" not in data:
                        yield from websocket.close()
                        return
                    else:
                        response = {"id": data["id"]}

                        # status query
                        try:
                            if data["id"] == 1:
                                response.update(APIStatus.handle(data, self._daemon))
                            # trigger new build
                            elif data["id"] == 2:
                                response.update(APITriggerBuild.handle(data, self._daemon))
                            # project list
                            elif data["id"] == 3:
                                response.update(APIProjectList.handle(data, self._daemon))
                            # view log
                            elif data["id"] == 4:
                                response.update(APIViewLog.handle(data, self._daemon))
                            else:
                                # close if an invalid packet was sent
                                yield from websocket.close()
                                return
                        except APIInvalidRequestException:
                            yield from websocket.close()
                            return
                        except APIUnauthorizedTokenException:
                            response.update({"error": "Access denied! Unauthorized token!"})
                        except APIErrorException as e:
                            response.update({"error": e.message})

                        # send response
                        yield from websocket.send(json.dumps(response))

                except ValueError:
                    yield from websocket.close()
                    return
            except ConnectionResetError:
                return
