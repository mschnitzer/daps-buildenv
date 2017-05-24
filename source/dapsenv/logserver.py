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

import os
import re
from dapsenv.general import LOG_DIR
from http.server import BaseHTTPRequestHandler

_logs_pattern = re.compile("^\/logs\/([a-zA-Z0-9\_\-]+)$")


class LogServer(BaseHTTPRequestHandler):

    def do_HEAD(s):
        s.send_response(200)
        s.send_header("Content-Type", "text")
        s.end_headers()

    def do_GET(s):
        match = _logs_pattern.match(s.path)

        if not match:
            s.send_response(404)
            s.send_header("Content-Type", "text")
            s.end_headers()

            s.wfile.write(b"Invalid link!")
        else:
            log_path = "{}/{}.log".format(LOG_DIR, match.groups()[0])

            if not os.path.isfile(log_path):
                s.send_response(404)
                s.send_header("Content-Type", "text")
                s.end_headers()

                s.wfile.write(b"Log file not found!")
            else:
                s.send_response(200)
                s.send_header("Content-Type", "text")
                s.end_headers()

                content = ""
                with open(log_path, "r") as logfile:
                    content = logfile.read()

                s.wfile.write(content.encode())

    def log_message(self, format, *args):
        return
