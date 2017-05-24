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

import copy
import dapsenv.configmanager as configmanager
import dapsenv.xslt as xslt
import grp
import json
import os
import pwd
import re
import sys
import threading
import time
from base64 import b64encode
from collections import OrderedDict
from dapsenv.actions.action import Action
from dapsenv.apiserver import APIServer
from dapsenv.autobuildconfig import AutoBuildConfig, _dcfiles_pattern
from dapsenv.daemonauth import DaemonAuth
from dapsenv.docker import Container
from dapsenv.dockerregistry import is_image_imported
from dapsenv.exceptions import (AutoBuildConfigurationErrorException,
                                UserNotInDockerGroupException, GitInvalidRepoException,
                                DockerImageMissingException, InvalidRootIDException,
                                GitErrorException)
from dapsenv.exitcodes import E_INVALID_GIT_REPO, E_DOCKER_IMAGE_MISSING
from dapsenv.general import (DAEMON_DEFAULT_INTERVAL, BUILDS_DIR, DAEMON_DEFAULT_MAX_CONTAINERS,
                             API_SERVER_DEFAULT_PORT, LOG_DIR, CONTAINER_IMAGE, DAEMON_AUTH_PATH)
from dapsenv.ircbot import IRCBot
from dapsenv.logmanager import log
from dapsenv.logserver import LogServer
from http.server import HTTPServer
from socket import gethostname


class Daemon(Action):
    def __init__(self):
        pass

    def execute(self, args):
        """@see Action.execute()
        """
        self._args = args

        # load settings and prepare daemon
        self._preperation()

        # check requirements
        self._checkDockerImage()

        # start IRC bot
        self._start_ircbot()

        # start api server
        if self._api_server == "true":
            api = APIServer("0.0.0.0", self._api_server_port, self)
            api.serve()

        # start log server if wanted
        if self._logserver:
            thread = threading.Thread(target=self._start_logserver)
            thread.start()

        # start daemon
        self.start()

    def _preperation(self):
        """Loads all settings and prepares the daemon
        """
        self._useirc = self._args["use_irc"]
        self._noout = self._args["no_output"]
        self._debug = self._args["debug"]
        self._logserver = self._args["use_logserver"]
        self._logserver_ip = self._args["logserver_ip"]
        self._logserver_port = self._args["logserver_port"]
        self._irc_config = {}
        self._ircbot = None
        self._logserver_httpd = None
        self._hostname = gethostname()
        self._auth = DaemonAuth(DAEMON_AUTH_PATH)

        self._daemon_info = {
            "jobs": [],
            "scheduled_builds": 0,
            "running_builds": 0
        }

        # create locks for thread-safe communications
        self._irclock = threading.Lock()
        self._daemon_info_lock = threading.Lock()

        # load daemon settings
        self.loadDaemonSettings()

        # load irc bot config
        self.loadIRCBotConfig()

        # load auto build configuration file
        if self._args["autobuild_config"]:
            self._autoBuildConfigFile = self._args["autobuild_config"]
        else:
            self._autoBuildConfigFile = configmanager.get_prop("daps_autobuild_config")

        self.autoBuildConfig = self.loadAutoBuildConfig(self._autoBuildConfigFile)

        # fetch all projects
        try:
            self.projects = self.autoBuildConfig.fetchProjects()
        except GitInvalidRepoException as e:
            log.error("Configuration error in auto build config '%s'! %s",
                      self._autoBuildConfigFile, e.message)
            sys.exit(E_INVALID_GIT_REPO)

    def _checkDockerImage(self):
        """Checks if the Docker Image is missing
        """

        try:
            self.checkRequirements()
        except DockerImageMissingException as e:
            log.error(e.message)
            sys.exit(E_DOCKER_IMAGE_MISSING)

    def _start_ircbot(self):
        if self._useirc:
            thread = threading.Thread(target=self._thread_ircbot)
            thread.start()

    def _thread_ircbot(self):
        # initialize bot
        self._ircbot = IRCBot(
            self._irc_config["irc_server"],
            self._irc_config["irc_server_port"],
            self._irc_config["irc_channel"],
            self._irc_config["irc_bot_nickname"],
            self._irc_config["irc_bot_username"]
        )

        self._ircbot.setDaemon(self)
        self._ircbot.start()

    def _start_logserver(self):
        """Starts the HTTP log server
        """

        self._logserver_httpd = HTTPServer(
            (self._logserver_ip, int(self._logserver_port)), LogServer
        )
        self._logserver_httpd.serve_forever()

    def start(self):
        """Starts the daemon
        """

        if not self._debug:
            self._print("The daemon is now running.")
        else:
            self._print("The daemon is now running in the debug mode.")

        # start thread which is required to handle incoming jobs
        thread = threading.Thread(target=self._jobManager)
        thread.start()

        # run check
        self.check()

        while True:
            time.sleep(self._interval)
            self.check()

    def _jobManager(self):
        while True:
            # get a list of all available jobs
            self._daemon_info_lock.acquire()
            running_builds = copy.copy(self._daemon_info["running_builds"])
            jobs = copy.copy(self._daemon_info["jobs"])
            self._daemon_info_lock.release()

            # search for new jobs in queue
            if running_builds < self._max_containers:
                for idx, job in enumerate(jobs):
                    if running_builds >= self._max_containers:
                        break

                    if job["status"] == 0:
                        # create thread
                        thread = threading.Thread(
                            target=self._process,
                            args=(copy.copy(job["project"]), job["dc_file"][:])
                        )

                        # start thread
                        thread.start()

                        # update amount of running builds
                        self._daemon_info_lock.acquire()

                        running_builds += 1

                        self._daemon_info["jobs"][idx]["status"] = 1
                        self._daemon_info["jobs"][idx]["time_started"] = int(time.time())
                        self._daemon_info["running_builds"] += 1
                        self._daemon_info["scheduled_builds"] -= 1

                        self._daemon_info_lock.release()
                    else:
                        break

            time.sleep(1)

    def check(self):
        """Starts docker containers if a documentation got updated
        """

        self._print("\nChecking for updates in documentation repositories...")

        # check and refresh all repositories
        self._prepare_build_task()

        self._print("Next scheduled check: {}".format(time.ctime(time.time() + self._interval)))

    def _prepare_build_task(self):
        """Goes through all specified repositories and updates those
        """

        for i in self.projects:
            # pull new commits into repository
            self.projects[i]["repo"].pull(self.projects[i]["vcs_branch"], force=True)

            # fetch current commit hash from branch
            commit = self.projects[i]["repo"].getLastCommitHash(self.projects[i]["vcs_branch"])

            # check if the last commit hash got changed
            if self.projects[i]["vcs_lastrev"] != commit:
                old_commit = self.projects[i]["vcs_lastrev"]

                # update to the new commit hash
                self.projects[i]["vcs_lastrev"] = commit[:]
                self.autoBuildConfig.updateCommitHash(self.projects[i]["project"], commit[:])

                # get changed files
                changed_files = []

                try:
                    changed_files = self.projects[i]["repo"].getChangedFilesBetweenCommits(
                        old_commit, commit
                    )
                except GitErrorException:
                    pass

                # determine assigned DC file for each changed file
                for dc_file, dc_object in self.projects[i]["dc_files"].items():
                    build = False

                    if dc_object.rootid:
                        try:
                            assigned_files = xslt.getAllUsedFiles(
                                "{}/xml/{}".format(self.projects[i]["vcs_repodir"], dc_object.main),
                                dc_object.rootid
                            )

                            # is at least one element from "changed_files" in "assigned_files"
                            res = lambda a, b: any(i in assigned_files for i in changed_files)

                            if res:
                                build = True
                        except InvalidRootIDException:
                            log.error("Invalid root id in main file '{}' of DC File '{}' specified. Repository: {}".format(
                                dc_object.main, dc_file, self.projects[i]["vcs_repodir"]
                            ))
                    else:
                        build = True

                    if build:
                        self._daemon_info_lock.acquire()
                        self._daemon_info["jobs"].append({"project": copy.copy(self.projects[i]),
                                                          "dc_file": dc_file[:],
                                                          "commit": commit[:],
                                                          "status": 0,
                                                          "container_id": "",
                                                          "time_started": 0
                                                          })

                        self._daemon_info["scheduled_builds"] += 1
                        self._daemon_info_lock.release()

    def _process(self, project_info, dc_file):
        """Thread function to start containers and build documentations

        :param dict project_info: A dictionary with information about that project
        :param string dc_file: DC what should get built
        """

        # forbid building of documentations in development mode
        if self._args["development"]:
            while True:
                time.sleep(30)

        # create container
        container = Container()
        container.spawn()

        # save container id in daemon info
        self._daemon_info_lock.acquire()

        for idx, job in enumerate(self._daemon_info["jobs"]):
            if job["dc_file"] == dc_file and job["status"] == 1:
                job["container_id"] = container.getContainerID()
                break

        self._daemon_info_lock.release()

        # prepare container
        container.prepare(project_info["vcs_repodir"])

        # specify build formats
        build_formats = ["html", "single_html", "pdf"]

        for f in build_formats:
            # building the documentation
            # pdb.set_trace()
            result = container.buildDocumentation(dc_file, f)

            archive = result["archive_name"]
            del result["archive_name"]

            # parse the documentation info
            product = json.loads(container.execute("cat /tmp/doc_info.json")["stdout"])

            # add new information to result dict
            result.update(product)

            # if debug mode is enabled, add some additional information to the
            # build_info.json file
            if self._debug:
                result["container_id"] = container.getContainerID()
            else:
                # remove the daps command from the result dictionary, if debug mode
                # is disabled
                del result["dapscmd"]

            if result["build_status"]:
                # generate a build info file for the documentation archive
                container.fileCreate("/tmp/build_info.json", json.dumps(result))

                # add build info file to documentation archive
                container.execute("tar -C /tmp --append --file={} build_info.json".format(archive))

                # compress tar archive
                container.execute("gzip {}".format(archive))

                # copy compiled documentation into the builds/ directory of the user
                file_name = "{}_{}_{}.tar.gz".format(int(time.time()), dc_file[3:], f.replace("_", "-"))
                container.fetch("{}.gz".format(archive), "{}/{}".format(
                    BUILDS_DIR, file_name
                ))

                self._irclock.acquire()

                if self._ircbot and self._irc_config["irc_inform_build_success"]:
                    message = "A new build has been finished on {}! DC-File: {}, Format: {}," \
                        " Output-Archive: {}".format(
                            self._hostname,
                            result["dc_file"],
                            result["format"],
                            file_name
                        )

                    for client in project_info["notifications"]["irc"]:
                        self._ircbot.sendClientMessage(client, message)

                    if self._irc_config["irc_channel_messages"]:
                        self._ircbot.sendChannelMessage(message)

                self._irclock.release()
            else:
                error_log_name = "build_fail_{}_{}_{}".format(
                    result["dc_file"],
                    result["format"],
                    int(time.time())
                )

                error_log_path = "{}/{}.log".format(
                    LOG_DIR,
                    error_log_name
                )

                if self._logserver:
                    irc_path = "http://{}:{}/logs/{}".format(
                        self._logserver_ip,
                        self._logserver_port,
                        error_log_name
                    )
                else:
                    irc_path = error_log_path

                with open(error_log_path, "w+") as f:
                    f.write(result["build_log"])

                self._irclock.acquire()

                if self._ircbot and self._irc_config["irc_inform_build_fail"]:
                    message = "A build has failed on {}! DC-File: {}, Format: {}, " \
                        "Error-Log: {}".format(
                            self._hostname,
                            result["dc_file"],
                            result["format"],
                            irc_path
                        )

                    for client in project_info["notifications"]["irc"]:
                        self._ircbot.sendClientMessage(client, message)

                    if self._irc_config["irc_channel_messages"]:
                        self._ircbot.sendChannelMessage(message)

                self._irclock.release()

            # execute cleanup script
            container.cleanup()

        # update amount of running builds
        self._daemon_info_lock.acquire()

        self._daemon_info["running_builds"] -= 1
        for idx, job in enumerate(self._daemon_info["jobs"]):
            if job["dc_file"] == dc_file and job["status"] == 1:
                self._daemon_info["jobs"].pop(idx)
                break

        self._daemon_info_lock.release()

        # kill and delete container from the registry
        if not self._debug:
            container.kill()

    def _print(self, message):
        """Prints messages to the CLI
        """

        if not self._noout:
            print(message)

    def scheduleProjectBuilds(self, projects):
        """Schedules one or more projects for building

        :param list projects: A list of project names to build
        :return list: A list of all successfully triggered project builds
        """

        self._daemon_info_lock.acquire()

        valid_projects = []

        for requested_project in set(projects):
            for idx in self.projects:
                project = self.projects[idx]
                if requested_project == project["project"]:
                    for dc_file in project["dc_files"]:
                        self._daemon_info["jobs"].append({
                            "project": copy.copy(project),
                            "dc_file": dc_file,
                            "commit": project["vcs_lastrev"],
                            "status": 0,
                            "container_id": "",
                            "time_started": 0
                        })

                        self._daemon_info["scheduled_builds"] += 1

                    valid_projects.append(project["project"])
                    break

        self._daemon_info_lock.release()

        return valid_projects

    def scheduleDCFileBuilds(self, dc_files):
        """Schedules one or more DC files for building

        :param list dc_files: A list of DC file names to build
        :return list: A list of all successfully triggered DC file builds
        """

        valid_dcs = []

        for dc_file in set(dc_files):
            for idx in self.projects:
                project = self.projects[idx]
                if dc_file in project["dc_files"]:
                    self._daemon_info_lock.acquire()
                    self._daemon_info["jobs"].append({
                        "project": copy.copy(self.projects[idx]),
                        "dc_file": dc_file[:],
                        "commit": project["vcs_lastrev"],
                        "status": 0,
                        "container_id": "",
                        "time_started": 0
                    })

                    self._daemon_info["scheduled_builds"] += 1
                    self._daemon_info_lock.release()

                    valid_dcs.append(dc_file)
                    break

        return valid_dcs

    def getJobList(self):
        result = []

        self._daemon_info_lock.acquire()
        for job in self._daemon_info["jobs"]:
            result.append({
                "project": job["project"]["project"],
                "branch": job["project"]["vcs_branch"],
                "dc_file": job["dc_file"],
                "status": job["status"],
                "commit": job["commit"],
                "time_started": job["time_started"],
                "status": job["status"]
            })
        self._daemon_info_lock.release()

        return result

    def getProjectNames(self):
        projects = OrderedDict()

        for idx in self.projects:
            project = self.projects[idx]
            projects[project["project"]] = list(project["dc_files"].keys())

        return projects

    @property
    def auth(self):
        return self._auth

    def loadAutoBuildConfig(self, path):
        """Loads the auto build config file into memory and parses it

        :param string path: Specifies the path where the file is stored
        """
        if not path:
            raise AutoBuildConfigurationErrorException()

        return AutoBuildConfig(path)

    def loadDaemonSettings(self):
        """Loads the settings for the daemon
        """

        self._current_builds = 0

        # daemon_check_interval
        try:
            self._interval = int(configmanager.get_prop("daemon_check_interval"))
        except TypeError:
            self._interval = DAEMON_DEFAULT_INTERVAL

        # daemon_max_containers
        try:
            self._max_containers = int(configmanager.get_prop("daemon_max_containers"))
        except TypeError:
            self._max_containers = DAEMON_DEFAULT_MAX_CONTAINERS

        # api_server
        self._api_server = configmanager.get_prop("api_server")

        # api_server_port
        try:
            self._api_server_port = int(configmanager.get_prop("api_server_port"))
        except TypeError:
            self._api_server_port = API_SERVER_DEFAULT_PORT

    def checkRequirements(self):
        """Check user requirements what are needed to run the daemon
        """

        # check if user is in docker group
        user = pwd.getpwuid(os.getuid()).pw_name
        user_in_group = False

        for group in grp.getgrall():
            if group.gr_name == "docker":
                if user in group.gr_mem:
                    user_in_group = True
                    break

        if not user_in_group:
            raise UserNotInDockerGroupException()

        # check if the docker image is imported
        if not is_image_imported(CONTAINER_IMAGE):
            raise DockerImageMissingException(CONTAINER_IMAGE)

    def getStatus(self):
        self._daemon_info_lock.acquire()
        daemon_info = self._daemon_info.copy()
        self._daemon_info_lock.release()

        return daemon_info

    def loadIRCBotConfig(self):
        self._irc_config["irc_server"] = configmanager.get_prop("irc_server")
        self._irc_config["irc_server_port"] = int(configmanager.get_prop("irc_server_port"))
        self._irc_config["irc_channel"] = "#{}".format(configmanager.get_prop("irc_channel"))
        self._irc_config["irc_bot_nickname"] = configmanager.get_prop("irc_bot_nickname")
        self._irc_config["irc_bot_username"] = configmanager.get_prop("irc_bot_username")
        self._irc_config["irc_inform_build_success"] = True if \
            configmanager.get_prop("irc_inform_build_success") == "true" else False
        self._irc_config["irc_inform_build_fail"] = True if \
            configmanager.get_prop("irc_inform_build_fail") == "true" else False
        self._irc_config["irc_channel_messages"] = True if \
            configmanager.get_prop("irc_channel_messages") == "true" else False
