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
from os import path

# specifies the current version of this program
__version__ = "1.0.0"

# the default pull interval for the daemon
DAEMON_DEFAULT_INTERVAL = 300

# max docker containers default value
DAEMON_DEFAULT_MAX_CONTAINERS = 15

# the directory where a repository should be copied in a container
CONTAINER_REPO_DIR = "/tmp/build"

# the name of the docker image
CONTAINER_IMAGE = "mschnitzer/dapsenv"

# source directory of this python project
SOURCE_DIR = path.dirname(path.realpath(__file__))

# home directory
HOME_DIR = "{}/.dapsenv".format(path.expanduser("~"))

# error log directory
LOG_DIR = "{}/logs".format(HOME_DIR)

# tmp directory
TMP_DIR = "{}/tmp".format(HOME_DIR)

# tmp directory
BUILDS_DIR = "{}/builds".format(HOME_DIR)

# templates location
TEMPLATE_PATH = "{}/templates".format(SOURCE_DIR)

# daemon-auth.xml file location
DAEMON_AUTH_PATH = "{}/daemon-auth.xml".format(HOME_DIR)

# token file
CLIENT_TOKEN_PATH = "{}/token".format(HOME_DIR)

# api server default port
API_SERVER_DEFAULT_PORT = 5555

# max token length
TOKEN_LENGTH = 32

# token validation pattern
TOKEN_PATTERN = re.compile("^[a-zA-Z0-9]+$")
