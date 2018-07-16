#!/usr/bin/python

# 
#   Copyright 2017 RIFT.IO Inc
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# Author: Aniruddha Atale

import hashlib
import basehash


class StringShortner(object):
    FOLDS = 3
    STRING_LEN=9
    def __init__(self, string = None):
        self._string = string

    @property
    def string(self):
        return self._string

    @string.setter
    def string(self, string):
        self._string = string

    @property
    def short_string(self):
        if self._string:
            return StringShortner._get_short_string(self._string)
        else:
            return str()

    @staticmethod
    def _fold_hex_series(series):
        length = len(series)
        result = list()
        for i in range(int(length/2)):
            result.append(series[i] ^ series[(length - 1) - i])

        if length % 2:
            result.append(series[int(length/2) + 1])

        return result

    @staticmethod
    def _num_from_hex_series(series):
        result = 0
        for i in range(len(series)):
            result = result * 256
            result += series[i]
        return result
    
    @staticmethod
    def _get_short_string(string):
        sha = hashlib.sha384(string.encode())
        digest = sha.digest()
        for i in range(StringShortner.FOLDS):
            digest = StringShortner._fold_hex_series(digest)

        number = StringShortner._num_from_hex_series(digest)
        base62 = basehash.base62(length=StringShortner.STRING_LEN)
        return base62.hash(number)
