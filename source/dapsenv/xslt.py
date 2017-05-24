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
from dapsenv.exceptions import XSLTProcException, InvalidRootIDException
from dapsenv.logmanager import log
from lxml import etree

_used_files_sheet_path = "{}/data/get-all-used-files.xsl".format(
    os.path.dirname(os.path.abspath(__file__))
)


def getAllUsedFiles(main, rootid):
    """Get all used files of an XML MAIN file

    :param string main: the main file of a documentation
    :param string rootid: the rootid of a DC file
    :return list: A list of all used files
    """

    xslt_tree = etree.parse(_used_files_sheet_path)
    transform = etree.XSLT(xslt_tree)

    main_tree = etree.parse(main,
                            etree.XMLParser(load_dtd=True, resolve_entities=True))

    result = transform(main_tree)
    rootid_elem = result.find("//div[@id='{}']".format(rootid))

    if rootid_elem is None:
        raise InvalidRootIDException(rootid)

    return set(rootid_elem.xpath(".//*/@href | .//*/@fileref"))
