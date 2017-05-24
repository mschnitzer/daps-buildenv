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
from dapsenv.exceptions import DCFileMAINNotFoundException


class DCFile:
    def __init__(self, path):
        self._path = path
        self._main = None
        self._main_path = None
        self._rootid = None

        self._search_pattern_main = re.compile("^MAIN\=(.*)$")
        self._search_pattern_rootid = re.compile("^ROOTID\=(.*)$")

        self.tryParse()

    def tryParse(self):
        with open(self._path, "r") as dcfile:
            for line in dcfile:
                if self._search_pattern_main.match(line):
                    self._main = self._getValue(line)
                    self._main_path = "{}/xml/{}".format(
                        os.path.dirname(os.path.realpath(self._path)),
                        self._main
                    )
                elif self._search_pattern_rootid.match(line):
                    self._rootid = self._getValue(line)

        if not self._main:
            raise DCFileMAINNotFoundException(self._path)

    def _getValue(self, line):
        line = line.strip("\n")
        pos = line.find("=")
        line = line[pos + 1:]

        if line[0] == '"':
            line = line[1:]

        if line[-1] == '"':
            line = line[:-1]

        return line

    @property
    def main(self):
        return self._main

    @property
    def main_path(self):
        return self._main_path

    @property
    def rootid(self):
        return self._rootid

    @property
    def path(self):
        return self._path
