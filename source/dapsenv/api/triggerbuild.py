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

from dapsenv.exceptions import APIInvalidRequestException, APIUnauthorizedTokenException


def handle(data, daemon):
    # check for correct data packages
    if "dc_files" not in data or "projects" not in data or "token" not in data:
        raise APIInvalidRequestException()

    if not isinstance(data["dc_files"], list) or not isinstance(data["projects"], list):
        raise APIInvalidRequestException()

    # check token
    if not data["token"] in daemon.auth.tokens:
        raise APIUnauthorizedTokenException()

    # schedule builds
    valid_projects = daemon.scheduleProjectBuilds(data["projects"])
    valid_dcs = daemon.scheduleDCFileBuilds(data["dc_files"])

    # answer
    return {
        "dc_files": valid_dcs,
        "projects": valid_projects
    }
