
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

import abc

def get_operation(operation):

    op_map = {"AND": AndScalingOperation(),
              "OR": OrScalingOperation()}

    return op_map[operation]


class ScalingOperation:
    @abc.abstractmethod
    def __call__(self, statuses):
        pass


class AndScalingOperation():
    def __call__(self, statuses):
        return all(statuses)


class OrScalingOperation():
    def __call__(self, statuses):
        return any(statuses)
