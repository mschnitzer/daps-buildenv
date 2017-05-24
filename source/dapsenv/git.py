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

import shlex
import subprocess
from dapsenv.exceptions import (GitInvalidRepoException, GitInvalidBranchName,
                                GitErrorException)
from dapsenv.logmanager import log


class Repository:
    def __init__(self, repo):
        """Initializes the Repository class

        :param string repo: The path to the repository
        """

        self._repopath = repo

        if not self._isGitRepo():
            raise GitInvalidRepoException(repo)

    def checkout(self, branch):
        """Checks out the given branch
        """

        process = subprocess.Popen(
            shlex.split("git -C {} checkout {}".format(self.getRepoPath(), branch)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if "did not match any" in process.stderr.read().decode("utf-8"):
            raise GitInvalidBranchName(self.getRepoPath(), branch)

    def branch(self):
        """Returns the name of the current branch

        :return string: Branch-Name
        """

        process = subprocess.Popen(
            shlex.split("git -C {} rev-parse --abbrev-ref HEAD".format(self.getRepoPath())),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        return process.stdout.read().decode("utf-8")[:-1]

    def pull(self, branch, force=False):
        """Pulls new commits from the git server

        :param string branch: The branch which should be updated
        :param bool force: Forces the pull
        """

        options = ""
        if force:
            options = " --force"

        # switch to the specified branch to update it
        self.checkout(branch)

        # perform 'pull' on branch
        with open("/dev/null", "w") as devnull:
            cmd = "git -C {} pull{}".format(self.getRepoPath(), options)

            subprocess.Popen(
                shlex.split(cmd),
                stdout=devnull,
                stderr=devnull
            )

    def getLastCommitHash(self, branch):
        """Fetches the last commit hash of a branch

        :param string branch: Name of the branch
        """

        cmd = "git --no-pager -C {} log -n 1 --pretty=format:\"%H\" {}".format(
            self.getRepoPath(), branch
        )

        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if "path not in the" in process.stderr.read().decode("utf-8"):
            raise GitInvalidBranchName(self.getRepoPath(), branch)

        return process.stdout.read().decode("utf-8")

    def getChangedFilesBetweenCommits(self, commit_1, commit_2):
        """Returns a list of changed files between two commits

        :param string commit_1: Oldest Commit
        :param string commit_2: Newest Commit
        :return list: Changed files
        """

        cmd = "git --no-pager -C {} diff --name-only {} {}".format(
            self._repopath,
            commit_1,
            commit_2
        )

        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stdout = process.stdout.read().decode("utf-8")
        stderr = process.stderr.read().decode("utf-8")

        if stderr:
            raise GitErrorException(cmd, stderr)

        return list(filter(None, stdout.split("\n")))

    def getRepoPath(self):
        """Gets the full path to the repository which was specified in __init__

        :return string: Full path to the repository
        """

        return self._repopath

    def _isGitRepo(self):
        """Checks if the specified directory is a git repository

        :return bool: true = is a git repository | false = is not a git repository
        """

        cmd = "git -C {} rev-parse --git-dir".format(self._repopath)
        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if len(process.stderr.read().decode("utf-8")):
            return False

        return True
