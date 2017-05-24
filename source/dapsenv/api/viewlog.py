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
from base64 import b64encode
from dapsenv.autobuildconfig import _dcfiles_pattern
from dapsenv.exceptions import APIInvalidRequestException, APIErrorException
from dapsenv.general import LOG_DIR


def handle(data, daemon):
    if "dc_file" not in data or "format" not in data:
        raise APIInvalidRequestException()

    dc_file = data["dc_file"]
    format_name = data["format"]

    if not _dcfiles_pattern.match(dc_file):
        raise APIErrorException("The DC-File name is not valid!")

    if format_name != "html" and format_name != "single_html" and format_name != "pdf":
        raise APIErrorException("Format is not valid. Please choose between: html, single_html, and pdf")

    pattern = re.compile("^build\_fail\_([a-zA-Z0-9\-]+)\_{}\_([0-9]+)\.log$".format(format_name))

    results = []
    files = os.listdir(LOG_DIR)
    for file_name in files:
        match = pattern.match(file_name)
        if match:
            res = match.groups()
            if res[0] == dc_file:
                results.append(res[1])

    content = ""

    if not results:
        raise APIErrorException("No log entries found for this DC-File and Format!")
    else:
        results.sort()

        with open("{}/build_fail_{}_{}_{}.log".format(LOG_DIR, dc_file, format_name, results[0]), "r") as log_file:
            content = log_file.read()

    return {"log": b64encode(content.encode("ascii")).decode("ascii")}
