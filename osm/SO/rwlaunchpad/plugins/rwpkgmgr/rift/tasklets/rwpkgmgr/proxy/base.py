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
# Author(s): Varun Prasad
# Creation Date: 09/25/2016
# 


import abc
import asyncio


class AbstractPackageManagerProxy():
    """Proxy interface that need to be implemented by the package store
    """
    @abc.abstractmethod
    @asyncio.coroutine
    def endpoint(self, package_type, package_id):
        """Rest based endpoint to reveal the package contents

        Args:
            package_type (str): NSD, VNFD
            package_id (str) ID
        
        Returns:
            str: URL of the endpoint
        
        """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def schema(self, package_type):
        """Summary
        
        Args:
            package_type (str): Type of package (NSD|VNFD)
        
        Returns:
            list: List of top level dirs
        
        """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def package_file_add(self, new_file, package_type, package_id, package_path):
        """Add file to a package
        
        Args:
            new_file (str): Path to the new file
            package_type (str): NSD,VNFD
            package_id (str): ID
            package_path (str): relative path into the package.
        
        Returns:
            Bool: True, If operation succeeded.
        """
        pass

    @abc.abstractmethod
    @asyncio.coroutine
    def package_file_delete(self, package_type, package_id, package_path):
        """delete file from a package
        
        Args:
            package_type (str): NSD,VNFD
            package_id (str): ID
            package_path (str): relative path into the package.
        
        Returns:
            Bool: True, If operation succeeded.
        """
        pass
