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

import argparse
import dapsenv.configmanager as configmanager
from dapsenv.general import __version__


class ArgParser:

    def __init__(self, args):
        self.args = args
        self.parser = argparse.ArgumentParser(
            description="A build environment to build documentations with DAPS."
        )
        self.cmdSubParser = self.parser.add_subparsers(
            dest="action",
            title="Available subcommands",
        )

        self.addGlobalOptions()
        self.addConfigCommand()
        self.addDaemonCommand()
        self.addStatusCommand()
        self.addTriggerBuildCommand()
        self.addProjectListCommand()
        self.addTokenCommand()
        self.addTokenAuthorizeCommand()
        self.addTokenDeauthorizeCommand()
        self.addViewLogCommand()

    def print_help(self):
        self.parser.print_help()

    def parse(self):
        return vars(self.parser.parse_args(args=self.args))

    def addGlobalOptions(self):
        self.parser.add_argument(
            "--version", action="version", help="Displays the current version of this program.",
            version="DAPS Build Environment Version {}".format(__version__)
        )

        self.parser.add_argument(
            "-v", "--verbose", action="count", help="Increase verbosity level"
        )

    def addConfigCommand(self):
        cmd = self.cmdSubParser.add_parser(
            "config", aliases=["c"], help="Modifying the configuration file."
        )

        config_group = cmd.add_mutually_exclusive_group(required=True)

        config_group.add_argument(
            "--global", "-g", action="store_true", help="Specifies to use the global "
            "configuration which is stored in the configuration directory /etc."
        )

        config_group.add_argument(
            "--user", "-u", action="store_true", help="Specifies to use the user configuration "
            "which is stored in the home directory of the current user."
        )

        config_group.add_argument(
            "--own", "-o", action="store_true", help="Specifies to use an own specified "
            "configuration which needs to be specified by --path"
        )

        config_group.add_argument(
            "--generate", action="store_true", help="Generates a configuration file. The "
            "must be set via --path."
        )

        cmd.add_argument(
            "--force", action="store_true", help="Force the creation of a config file."
        )

        cmd.add_argument(
            "--path", action="store", help="Specifies a path to a configuration file."
        )

        cmd.add_argument(
            "--property", "-p", action="store",
            help="Specifies a property from the config file. If no value is set with --value, "
            "only the current value of the property will be print on the command line."
        )

        cmd.add_argument(
            "--value", action="store", help="Sets a new value for a property."
        )

    def addDaemonCommand(self):
        logmanager_ip = configmanager.get_prop("logmanager_ip")
        if not logmanager_ip:
            default_ip = "127.0.0.1"

        logserver_port = 5556
        try:
            logserver_port = int(configmanager.get_prop("logserver_port"))
        except ValueError:
            pass

        cmd = self.cmdSubParser.add_parser(
            "daemon", aliases=["d"], help="This command starts a daemon which takes care of "
            "the documentation building process."
        )

        cmd.add_argument(
            "--use-irc", "-i", action="store_true", help="Connects to the IRC server what is "
            "configured in the configuration file."
        )

        cmd.add_argument(
            "--use-logserver", "-l", action="store_true", help="Starts an HTTP server what "
            "provides access to build log files."
        )

        cmd.add_argument(
            "--logserver-ip", action="store", default=logmanager_ip, help="The IP address the log "
            "server should listen to."
        )

        cmd.add_argument(
            "--logserver-port", action="store", default=logserver_port, help="The IP address the log "
            "server should listen to."
        )

        cmd.add_argument(
            "--no-output", "-n", action="store_true", help="Hides the daemon output."
        )

        cmd.add_argument(
            "--debug", "-d", action="store_true", help="Useful for developer to get more "
            "information about the Daemon process."
        )

        cmd.add_argument(
            "--autobuild-config", "-a", action="store", help="Specifies a path to the "
            "autobuild config file. This overrides the value in configuration files."
        )

        cmd.add_argument(
            "--development", action="store_true", help="Not relevant for the normal user and "
            "should only be used by developers. This option forbids to start docker containers. "
            "This is useful during development."
        )

    def addStatusCommand(self):
        default_ip = configmanager.get_prop("api_client_default_ip")
        if not default_ip:
            default_ip = "127.0.0.1"

        default_port = 5555
        try:
            default_port = int(configmanager.get_prop("api_client_default_port"))
        except ValueError:
            pass

        cmd = self.cmdSubParser.add_parser(
            "status", aliases=["s"], help="Queries a DapsEnv API server."
        )

        cmd.add_argument(
            "--ip", "-i", action="store", default=default_ip,
            help="Sets the IP of the API server."
        )

        cmd.add_argument(
            "--port", "-p", action="store", default=default_port,
            help="Sets the port of the API server."
        )

    def addTriggerBuildCommand(self):
        default_ip = configmanager.get_prop("api_client_default_ip")
        if not default_ip:
            default_ip = "127.0.0.1"

        default_port = 5555
        try:
            default_port = int(configmanager.get_prop("api_client_default_port"))
        except ValueError:
            pass

        cmd = self.cmdSubParser.add_parser(
            "trigger-build", aliases=["tb"], help="Triggers a build on a DapsEnv instance."
        )

        cmd.add_argument(
            "--ip", "-i", action="store", default=default_ip,
            help="Sets the IP of the API server."
        )

        cmd.add_argument(
            "--port", "-p", action="store", default=default_port,
            help="Sets the port of the API server."
        )

        cmd.add_argument(
            "--projects", "-r", nargs="+", action="store",
            help="Schedules builds for the given projects."
        )

        cmd.add_argument(
            "--dcfiles", "-d", nargs="+", action="store",
            help="Schedules builds for the given DC-Files."
        )

    def addProjectListCommand(self):
        default_ip = configmanager.get_prop("api_client_default_ip")
        if not default_ip:
            default_ip = "127.0.0.1"

        default_port = 5555
        try:
            default_port = int(configmanager.get_prop("api_client_default_port"))
        except ValueError:
            pass

        cmd = self.cmdSubParser.add_parser(
            "project-list", aliases=["pl"], help="Retrieves a list of all projects on a "
            "DapsEnv instance."
        )

        cmd.add_argument(
            "--ip", "-i", action="store", default=default_ip,
            help="Sets the IP of the API server."
        )

        cmd.add_argument(
            "--port", "-p", action="store", default=default_port,
            help="Sets the port of the API server."
        )

    def addTokenCommand(self):
        cmd = self.cmdSubParser.add_parser(
            "token", aliases=["t"], help="Manage the client token."
        )

        cmd.add_argument(
            "--regenerate-token", "-r", action="store_true", help="Forces a regeneration of the "
            "client token."
        )

    def addTokenAuthorizeCommand(self):
        cmd = self.cmdSubParser.add_parser(
            "token-authorize", aliases=["ta"], help="Authorizes one or more tokens for Daemon "
            "commands."
        )

        cmd.add_argument(
            "tokens", nargs="+", metavar="TOKENS", help="A list (separated by spaces) of tokens "
            "to authorize."
        )

    def addTokenDeauthorizeCommand(self):
        cmd = self.cmdSubParser.add_parser(
            "token-deauthorize", aliases=["td"], help="Deauthorizes one or more tokens from "
            "issuing Daemon commands."
        )

        cmd.add_argument(
            "tokens", nargs="+", metavar="TOKENS", help="A list (separated by spaces) of tokens "
            "to deauthorize."
        )

    def addViewLogCommand(self):
        default_ip = configmanager.get_prop("api_client_default_ip")
        if not default_ip:
            default_ip = "127.0.0.1"

        default_port = 5555
        try:
            default_port = int(configmanager.get_prop("api_client_default_port"))
        except ValueError:
            pass

        cmd = self.cmdSubParser.add_parser(
            "view-log", aliases=["vl"], help="Shows the log result of a failed build."
        )

        cmd.add_argument(
            "--ip", "-i", action="store", default=default_ip,
            help="Sets the IP of the API server."
        )

        cmd.add_argument(
            "--port", "-p", action="store", default=default_port,
            help="Sets the port of the API server."
        )

        cmd.add_argument(
            "--format", "-f", action="store", required=True,
            choices=["html", "single_html", "pdf"], help="Format of the documentation."
        )

        cmd.add_argument(
            "DC-FILE", nargs=1, action="store",
            help="Name of the DC-File."
        )
