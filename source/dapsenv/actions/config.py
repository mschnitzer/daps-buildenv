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

import dapsenv.configmanager as configmanager
import sys
from dapsenv.actions.action import Action
from dapsenv.exceptions import (ConfigPropertyNotFoundException, InvalidCommandLineException,
                                ConfigFileAlreadyExistsException,
                                ConfigFileCreationPermissionErrorException)
from dapsenv.exitcodes import E_CONFIG_FILE_PERMISSION_DENIED, E_CONFIG_FILE_ALREADY_CREATED
from dapsenv.logmanager import log


class Config(Action):
    def __init__(self):
        pass

    def execute(self, args):
        """@see Action.execute()
        """

        self._args = args
        self._path = args["path"]

        # determine wished configuration type
        self._determine_config_type()

        # check command line
        self._check_command_line()

        if self._args["generate"]:
            self.generate_config(self._args["path"])
        else:
            # check if the user either wants to modify the configuration or to just get the
            # value of a property
            if not args["value"]:
                self.get_property(self._args["property"])
            else:
                self.set_property(self._args["property"], self._args["value"])

    def get_property(self, prop):
        """Displays the value of the wanted property

        :param string prop: The name of the property
        """

        value = configmanager.get_prop(prop, self._configtype, self._path)
        if value:
            print(configmanager.get_prop(prop, self._configtype, self._path))
        else:
            raise ConfigPropertyNotFoundException()

    def set_property(self, prop, value):
        """Sets a property of a value

        :param string prop: The name of the property
        :param string value: The value to be set
        """

        configmanager.set_prop(prop, value, self._configtype, self._path)

    def generate_config(self, path):
        """It generates a configuration file at the desired location

        :param string path: The path where the config file should be generated
        """

        try:
            configmanager.generate_config(path, self._args["force"])
        except ConfigFileAlreadyExistsException as e:
            log.error("There is already a file called 'dapsenv.conf' in the directory '%s'. "
                      "Use --force to overwrite that file.", e.path)
            sys.exit(E_CONFIG_FILE_ALREADY_CREATED)
        except ConfigFileCreationPermissionErrorException as e:
            log.error("Could not create config file at '%s'. Permission denied.", e.path)
            sys.exit(E_CONFIG_FILE_PERMISSION_DENIED)

        print("The configuration file got successfully created at: {}".format(path))

    def _check_command_line(self):
        """Checks if the command line options are set properly
        """

        if (self._configtype == "own" or self._args["generate"]) and not self._path:
            raise InvalidCommandLineException("You need to specify a path with --path for the "
                                              "options --own and --generate.")
        elif not self._configtype == "own" and not self._args["generate"] and self._path:
            raise InvalidCommandLineException("Option --path is only required in combination "
                                              "with --own or --generate.")

        if (self._args["global"] or self._args["user"] or self._args["own"]) and not self._args["property"]:
            raise InvalidCommandLineException("You need to specify --property.")

    def _determine_config_type(self):
        """Determines the configuration type
        """
        self._configtype = None

        if self._args["global"]:
            self._configtype = "global"
        elif self._args["user"]:
            self._configtype = "user"
        elif self._args["own"]:
            self._configtype = "own"
