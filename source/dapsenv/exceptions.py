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

import sys
from dapsenv.exitcodes import (E_INVALID_CLI, E_NO_IMPLEMENTATION_FOUND, E_CONFIG_PROP_NOT_FOUND,
                               E_CONFIG_FILE_PERMISSION_DENIED, E_CONFIG_FILE_NOT_CREATED,
                               E_CONFIG_AUTOBUILD_ERROR, E_AUTOBUILDCONFIG_SYNTAX_ERROR,
                               E_AUTOBUILDCONFIG_NOT_FOUND, E_NOT_DOCKER_GROUP_MEMBER)
from dapsenv.general import TOKEN_LENGTH
from dapsenv.logmanager import log


class DapsEnvException(Exception):
    pass


class InvalidCommandLineException(DapsEnvException):
    def __init__(self, message=""):
        if len(message):
            log.error(message)

        sys.exit(E_INVALID_CLI)


class InvalidActionException(DapsEnvException):
    def __init__(self, action):
        log.error("No implementation for '%s' found.", action)
        sys.exit(E_NO_IMPLEMENTATION_FOUND)


class InvalidConfigTypeException(DapsEnvException):
    pass


class ConfigPropertyNotFoundException(DapsEnvException):
    def __init__(self):
        sys.exit(E_CONFIG_PROP_NOT_FOUND)


class ConfigFilePermissionErrorException(DapsEnvException):
    def __init__(self, file_name):
        log.error("Could not access config file '%s'! Please check the permissions.", file_name)
        sys.exit(E_CONFIG_FILE_PERMISSION_DENIED)


class ConfigFileNotCreatedException(DapsEnvException):
    def __init__(self, file_name):
        log.error("Config file '%s' does not exist. Please generate it by using: 'dapsenv "
                  "config --generate --path %s'", file_name, file_name)
        sys.exit(E_CONFIG_FILE_NOT_CREATED)


class ConfigFileCreationPermissionErrorException(DapsEnvException):
    def __init__(self, path):
        self.path = path


class ConfigFileAlreadyExistsException(DapsEnvException):
    def __init__(self, path):
        self.path = path


class AutoBuildConfigurationErrorException(DapsEnvException):
    def __init__(self):
        log.error("The property 'daps_autobuild_config' is not configured in the configuration file.")
        sys.exit(E_CONFIG_AUTOBUILD_ERROR)


class AutoBuildConfigSyntaxErrorException(DapsEnvException):
    def __init__(self, path, error):
        log.error("The auto build configuration file '%s' is invalid. Error: %s",
                  path, error)
        sys.exit(E_AUTOBUILDCONFIG_SYNTAX_ERROR)


class AutoBuildConfigNotFound(DapsEnvException):
    def __init__(self, path):
        log.error("The auto build config file '%s' could not be found.", path)
        sys.exit(E_AUTOBUILDCONFIG_NOT_FOUND)


class UserNotInDockerGroupException(DapsEnvException):
    def __init__(self):
        log.error("The current user is not a member of the 'docker' group. If you recently "
                  "added yourself to the 'docker' group, try to logout and back in again.")
        sys.exit(E_NOT_DOCKER_GROUP_MEMBER)


class ContainerNotSpawnedException(DapsEnvException):
    pass


class ContainerAlreadySpawnedException(DapsEnvException):
    pass


class ContainerPreparationMissingException(DapsEnvException):
    pass


class ContainerBuildFileNotAvailableException(DapsEnvException):
    pass


class UnexpectedStderrOutputException(DapsEnvException):
    def __init__(self, command, stderr):
        self.command = command
        self.stderr = stderr

    def __str__(self):
        log.error("Unexpected stderr for command '%s' caught: %s",
                  self.command, self.stderr)


class GitInvalidRepoException(DapsEnvException):
    def __init__(self, repo):
        self.repo = repo
        self.message = "Path '{}' is not a Git repository!".format(self.repo)

    def __str__(self):
        log.error(self.message)


class GitInvalidBranchName(DapsEnvException):
    def __init__(self, repo, branch):
        self.repo = repo
        self.branch = branch

        self.message = "Branch '{}' could not be found in repository '{}'.".format(self.repo, self.branch)

    def __str__(self):
        log.error(self.message)


class GitErrorException(DapsEnvException):
    def __init__(self, command, stderr):
        self.command = command
        self.stderr = stderr

    def __str__(self):
        log.error("Could not execute '%s': %s", self.command, self.stderr)


class ContainerFileCreationFailed(DapsEnvException):
    def __init__(self, file_name):
        self.file_name = file_name
        self.message = "Internal Error: File '{}' could not be created inside a container!".format(
            file_name
        )

    def __str__(self):
        log.error(self.message)


class DockerRegisteryException(DapsEnvException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        log.error(self.message)


class DockerImageMissingException(DapsEnvException):
    def __init__(self, image):
        self.image = image
        self.message = "Docker Image '{}' must be imported first! Run 'docker pull {}' " \
            "to import it.".format(image, image)

    def __str__(self):
        return self.message


class DCFileMAINNotFoundException(DapsEnvException):
    def __init__(self, dcfile):
        self.dcfile = dcfile
        self.message = "MAIN Variable not found in DC-File '{}'.".format(dcfile)

    def __str__(self):
        return self.message


class XSLTProcException(DapsEnvException):
    def __init__(self, command, stderr):
        self.command = command
        self.stderr = stderr
        self.message = "command '{}' has failed. stderr: {}".format(command, stderr)

    def __str__(self):
        return self.message


class InvalidRootIDException(DapsEnvException):
    def __init__(self, rootid):
        self.rootid = rootid
        self.message = "Unknown root id '{}'.".format(rootid)

    def __str__(self):
        return self.message


class AuthFileNotInitializedException(DapsEnvException):
    def __init__(self, file_name, message):
        self.file_name = file_name
        self.message = message

    def __str__(self):
        return self.message


class AuthFileParseException(DapsEnvException):
    def __init__(self, file_name, message):
        self.file_name = file_name
        self.message = message

    def __str__(self):
        return self.message


class InvalidTokenLengthException(DapsEnvException):
    def __init__(self, token):
        self.token = token
        self.message = "Invalid length of token '{}'. A token must " \
            "have a length of {} characters.".format(token, TOKEN_LENGTH)

    def __str__(self):
        return self.message


class InvalidTokenCharsException(DapsEnvException):
    def __init__(self, token):
        self.token = token
        self.message = "Token '{}' has invalid characters. A token must only have " \
            "letters and numbers.".format(token)

    def __str__(self):
        return self.message


class TokenAlreadyAuthorizedException(DapsEnvException):
    def __init__(self, token):
        self.token = token
        self.message = "Token '{}' is already authorized.".format(token)

    def __str__(self):
        return self.message


class TokenNotAuthorizedException(DapsEnvException):
    def __init__(self, token):
        self.token = token
        self.message = "Token '{}' is not authorized.".format(token)

    def __str__(self):
        return self.message


class APIInvalidRequestException(DapsEnvException):
    pass


class APIUnauthorizedTokenException(DapsEnvException):
    pass


class APIErrorException(DapsEnvException):
    def __init__(self, message):
        self.message = message
