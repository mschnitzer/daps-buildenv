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

import threading
from copy import copy
from dapsenv.exceptions import (AuthFileNotInitializedException, AuthFileParseException,
                                InvalidTokenLengthException, InvalidTokenCharsException,
                                TokenAlreadyAuthorizedException, TokenNotAuthorizedException)
from dapsenv.general import TOKEN_LENGTH, TOKEN_PATTERN
from lxml import etree


class DaemonAuth:

    def __init__(self, file_name):
        """Initializes a daemon-auth.xml file

        :param string file_name: A daemon-auth.xml file
        """

        self._file_name = file_name
        self._tree = None
        self._tokens_element = None
        self._tokens = []
        self._tokens_lock = threading.Lock()

        self.parse()

    def authorize(self, token):
        """Authorizes a new token for Daemon commands

        :param string token: Token
        """

        if not self._tree:
            raise AuthFileNotInitializedException(self._file_name)

        if len(token) != TOKEN_LENGTH:
            raise InvalidTokenLengthException(token)

        if not TOKEN_PATTERN.match(token):
            raise InvalidTokenCharsException(token)

        self._tokens_lock.acquire()

        if token in self._tokens:
            self._tokens_lock.release()
            raise TokenAlreadyAuthorizedException(token)

        token_elem = etree.Element("token", {"token": token})
        self._tokens_element.append(token_elem)
        self._save()

        self._tokens.append(token)
        self._tokens_lock.release()

    def deauthorize(self, token):
        """Deauthorize token from issuing Daemon commands

        :param string token: Token
        """

        if not self._tree:
            raise AuthFileNotInitializedException(self._file_name)

        self._tokens_lock.acquire()

        if token not in self._tokens:
            self._tokens_lock.release()
            raise TokenNotAuthorizedException(token)

        element = self._tree.xpath("//tokens/token[@token='{}']".format(token))[0]
        self._tokens_element.remove(element)
        self._save()

        self._tokens.remove(token)
        self._tokens_lock.release()

    def _save(self):
        """Saves the current state of the XML tee
        """

        if not self._tree:
            raise AuthFileNotInitializedException(self._file_name)

        self._tree.write(
            self._file_name, encoding="utf-8", xml_declaration=True, pretty_print=True
        )

    def parse(self):
        """Validates the daemon-auth.xml file
        """

        try:
            self._tree = etree.parse(self._file_name)
            self._tokens_element = self._tree.find("tokens")

            if self._tokens_element is None:
                raise AuthFileParseException(self._file_name, "No <tokens> element found.")

            for token in self._tokens_element:
                if "token" not in token.attrib:
                    raise AuthFileParseException(self._file_name,
                                                 "'token' attribute in 'token' "
                                                 "element is missing!")

                self._tokens.append(token.attrib["token"])

        except etree.XMLSyntaxError as e:
            raise AuthFileParseException(self._file_name, "XML Error: {}".format(e.message))

    @property
    def file_name(self):
        return self._file_name

    @property
    def tokens(self):
        self._tokens_lock.acquire()
        tokens = copy(self._tokens)
        self._tokens_lock.release()

        return tokens
