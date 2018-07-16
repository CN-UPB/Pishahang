
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

import functools

#from . import exceptions


def unsupported(f):
    @functools.wraps(f)
    def impl(*args, **kwargs):
        msg = '{} not supported'.format(f.__name__)
        raise exceptions.RWErrorNotSupported(msg)

    return impl


class Topology(object):
    """
    Topoology defines a base class for sdn driver implementations. Note that
    not all drivers will support the complete set of functionality presented
    here.
    """

    @unsupported
    def get_network_list(self, account):
        """
        Returns the discovered network associated with the specified account.

        @param account - a SDN account

        @return a discovered network
        """
        pass

