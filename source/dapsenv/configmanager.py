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

import re
import shutil
import os
from dapsenv.exceptions import (InvalidConfigTypeException, ConfigFilePermissionErrorException,
                                ConfigFileNotCreatedException, ConfigFileAlreadyExistsException,
                                ConfigFileCreationPermissionErrorException)
from os.path import expanduser, isfile

_search_pattern = re.compile("(?!#)(?P<key>[\w\d]+)\s*=\s*(?P<value>.*)")


def get_prop(prop, config_type="", config_path=""):
    """Returns the value of a property - should be used from other modules only!

    :param string prop: The requested property
    :param string config_type: The type of the config (global, user, own)
    :param string config_path: Sets the path for a configuration file (only required if "own"
                               is set in config_type)
    :return string: The value of the property or None
    """
    paths = []

    if len(config_type):
        paths = [get_config_path(config_type, config_path)]
    else:
        paths = [get_global_config_path()]

        user_path = get_user_config_path()
        if os.path.exists(user_path):
            paths.append(user_path)

    return get_property_value(prop, paths)


def set_prop(prop, value, config_type="", config_path=""):
    """Sets the value of a property - should be used from other modules only!

    :param string prop: The requested property
    :param string value: The value to be set
    :param string config_type: The type of the config (global, user, own)
    :param string config_path: Sets the path for a configuration file (only required if "own"
                               is set in config_type)
    """
    path = get_config_path(config_type, config_path)
    set_property_value(prop, value, path)


def get_config_path(config_type, config_path=""):
    """Resolves a path for a config type

    :param string config_type: Sets the type of the wanted configuration file (global, user, own)
    :param string config_path: Will be returned if "own" is set as config_type
    :return string: a config path
    """
    data = {"own": config_path,
            "user": get_user_config_path(),
            "global": get_global_config_path()
            }

    try:
        return data[config_type]
    except KeyError:
        raise InvalidConfigTypeException()


def get_global_config_path():
    """Returns the path of the global configuration file

    :return string: Path to the global configuration file
    """
    return "/etc/dapsenv/dapsenv.conf"


def get_user_config_path():
    """Returns the path of the user configuration file

    :return string: Path to the user configuration file
    """
    return "{}/.dapsenv/dapsenv.conf".format(expanduser("~"))


def get_property_value(prop, paths):
    """Returns the value of a property - should only be used internally!

    :param string prop: Name of the property
    :param list paths: The paths to look for configuration files
    :return string|None: The value of the given property or None if no appropriate property was
                         found
    """
    data = parse_config(paths)
    return data.get(prop)


def set_property_value(prop, value, path):
    """Sets a value for a property - should only be used internally!

    :param string prop: Name of the property
    :param string path: The path to the configuration file
    """
    if not isfile(path):
        raise ConfigFileNotCreatedException(path)

    content = ""
    updated = False

    try:
        with open(path, "r+") as f:
            for line in f:
                m = _search_pattern.search(line)

                if m:
                    result = m.groupdict()

                    # check if the found property matches with the wanted property
                    if result["key"] == prop:
                        content += "{}={}\n".format(prop, value)
                        updated = True
                        continue

                content += line

            # if the last character is a newline, remove it
            if len(content) and content[-1] == "\n":
                content = content[:-1]

            # create a new entry if we property does not yet exist
            if not updated:
                content += "\n{}={}".format(prop, value)

            # overwrite old config file content
            f.seek(0)
            f.truncate()
            f.write(content)
    except PermissionError:
        raise ConfigFilePermissionErrorException(path)


def parse_config(paths):
    """Parses all given configuration files and returns their content

    :param list paths: A list of configuration files what should be parsed
    :return dict: All key-value pairs what were found in all of the given configuration files.
                  Duplicate entries will be overwritten by the next configuration file.
    """

    data = {}

    try:
        for path in paths:
            if not isfile(path):
                raise ConfigFileNotCreatedException(path)

            with open(path) as f:
                for line in f:
                    # search for key=value pairs
                    m = _search_pattern.search(line)

                    if m:
                        result = m.groupdict()
                        data[result["key"]] = result["value"]

        return data
    except PermissionError:
        raise ConfigFilePermissionErrorException(path)


def generate_config(path, force_overwrite=False):
    """Generates a configuration file at the desired location

    :param string path: Desired location
    :param bool force_overwrite: Specifies if the file does already exist if
                                 it should be overwritten
    """

    currdir = os.path.dirname(os.path.realpath(__file__))

    if not force_overwrite:
        if os.path.exists("{}/dapsenv.conf".format(path)):
            raise ConfigFileAlreadyExistsException(path)

    try:
        shutil.copy("{}/templates/dapsenv.conf".format(currdir), path)
    except PermissionError:
        raise ConfigFileCreationPermissionErrorException(path)
