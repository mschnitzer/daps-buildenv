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
from dapsenv.exceptions import DockerRegisteryException


def is_image_imported(imagename):
    with open("/dev/null", "r") as devnull:
        process = subprocess.Popen(
            shlex.split("docker images -q {}".format(imagename)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        stderr = process.stderr.read().decode("utf-8")
        stdout = process.stdout.read().decode("utf-8")

        if stderr:
            raise DockerRegisteryException(stderr)

        if stdout:
            return True

    return False
