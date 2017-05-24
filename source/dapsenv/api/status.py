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


def handle(data, daemon):
    jobs = daemon.getJobList()

    running_builds = sum(1 for j in jobs if j["status"] == 1)
    scheduled_builds = sum(1 for j in jobs if j["status"] == 0)

    return {"running_builds": running_builds,
            "scheduled_builds": scheduled_builds,
            "jobs": jobs
            }
