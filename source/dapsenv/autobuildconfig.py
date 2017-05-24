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

import dapsenv.git as Git
import re
import threading
from collections import OrderedDict
from dapsenv.dcfile import DCFile
from dapsenv.exceptions import AutoBuildConfigSyntaxErrorException, AutoBuildConfigNotFound
from lxml import etree
from lxml.etree import XMLSyntaxError

_dcfiles_pattern = re.compile("DC\-[a-zA-Z0-9\-_]+")


class AutoBuildConfig:

    def __init__(self, path):
        """Initializes the AutoBuildConfig class

        :param string path: The path to the auto build config file
        """

        self._path = path
        self._write_lock = threading.Lock()
        self.parse()

    def parse(self):
        """Parses the given auto build config file
        """

        try:
            self._tree = etree.parse(self._path)
        except XMLSyntaxError as e:
            raise AutoBuildConfigSyntaxErrorException(self._path, e)
        except IOError:
            raise AutoBuildConfigNotFound(self._path)

    def fetchProjects(self):
        """returns all 'set' elements as a well formed structure

        :return OrderedDict: a structure with all projects and their details
        """

        data = OrderedDict()
        projects = self._tree.findall("set")

        for index, project in enumerate(projects):
            project_name = project.attrib["id"]
            dc_files = project.find("dcfiles").text
            vcs_data = project.find("vcs")

            data[index] = {}
            data[index]["project"] = project_name
            data[index]["vcs"] = vcs_data.attrib["type"]
            data[index]["vcs_branch"] = vcs_data.attrib["branch"]
            data[index]["vcs_type"] = vcs_data.attrib["type"]
            data[index]["vcs_repodir"] = vcs_data.find("checkout").text
            data[index]["vcs_lastrev"] = vcs_data.find("lastrev").text
            data[index]["repo"] = Git.Repository(data[index]["vcs_repodir"])
            data[index]["maintainer"] = project.find("maintainer").text
            data[index]["meta"] = project.attrib["meta"]
            data[index]["remarks"] = project.attrib["remarks"]
            data[index]["draft"] = project.attrib["draft"]
            data[index]["notifications"] = {}
            data[index]["notifications"]["emails"] = []
            data[index]["notifications"]["irc"] = []
            data[index]["dc_files"] = self._parse_dc_files(
                vcs_data.find("checkout").text,
                dc_files,
                data[index]["repo"],
                data[index]["vcs_branch"]
            )

            notification_elem = project.find("notifications")

            if notification_elem is not None:
                email_elem = notification_elem.find("emails")
                if email_elem is not None:
                    data[index]["notifications"]["emails"] = email_elem.text.split()

                irc_elem = notification_elem.find("irc")
                if irc_elem is not None:
                    data[index]["notifications"]["irc"] = irc_elem.text.split()

        return data

    def updateCommitHash(self, project, new_commit):
        """Updates the commit hash for a project thread-safe

        :param string project: the name of the project
        :param string new_commit: The new commit hash
        """

        self._write_lock.acquire()

        el = self._tree.find("set[@id='{}']/vcs/lastrev".format(project))
        if el != -1:
            el.text = new_commit
            self._tree.write(self._path, encoding="utf-8", xml_declaration=True)

        self._write_lock.release()

    def _parse_dc_files(self, repo_dir, dc_files, repo, branch):
        """Remove all trash characters from the 'dcfiles' element

        :param string repo_dir: path to the Repository
        :param string dc_files: the content of the <dcfiles/> element
        :param Git.Repository repo: The repository object
        :param string branch: The branch for the documentation
        :return OrderedDict: A dict with all dc_files
        """

        dcs = _dcfiles_pattern.findall(dc_files)
        dc_files = OrderedDict()

        for dc in dcs:
            # switch to given branch
            currbranch = repo.branch()
            if currbranch != branch:
                repo.checkout(branch)

            dc_files[dc] = DCFile("{}/{}".format(repo_dir, dc))

            # switch back to other branch
            if currbranch != branch:
                repo.checkout(currbranch)

        return dc_files
