
# 
#   Copyright 2016 RIFT.IO Inc
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

import hashlib
import re

def checksum_string(s):
    return hashlib.md5(s.encode('utf-8')).hexdigest()


def checksum(fd):
    """ Calculate a md5 checksum of fd file handle

    Arguments:
      fd: A file descriptor return from open() call

    Returns:
      A md5 checksum of the file

    """
    pos = fd.tell()
    try:
        current = hashlib.md5()
        while True:
            data = fd.read(2 ** 16)
            if len(data) == 0:
                return current.hexdigest()
            current.update(data)
    finally:
        fd.seek(pos)


class ArchiveChecksums(dict):
    @classmethod
    def from_file_desc(cls, fd):
        checksum_pattern = re.compile(r"(\S+)\s+(\S+)")
        checksums = dict()

        pos = fd.tell()
        try:
            for line in (line.decode('utf-8').strip() for line in fd if line):

                # Skip comments
                if line.startswith('#'):
                    continue

                # Skip lines that do not contain the pattern we are looking for
                result = checksum_pattern.search(line)
                if result is None:
                    continue

                chksum, filepath = result.groups()
                checksums[filepath] = chksum

        finally:
            fd.seek(pos)

        return cls(checksums)

    def to_string(self):
        string = ""
        for file_name, file_checksum in self.items():
            string += "{}  {}\n".format(file_checksum, file_name)

        return string
