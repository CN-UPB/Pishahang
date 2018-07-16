#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# Copyright 2016-2017 VMware Inc.
# This file is part of ETSI OSM
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# For those usages not covered by the Apache License, Version 2.0 please
# contact:  osslegalrouting@vmware.com
##

import threading
import sys

class RepeatingTimer(threading._Timer):
    """ Class to run thread parally """
    def run(self):
        """ Method to run thread """
        while True:
            self.finished.wait(self.interval)
            if self.finished.is_set():
                return
            else:
                self.function(*self.args, **self.kwargs)


class CommandProgressbar(object):
    """ Class to show progressbar while waiting fro command output """

    def __init__(self):
        self.timer = None

    def __show_progressbar(self):
        """
            Private method to show progressbar while waiting for command to complete
            Args  : None
            Return : None
        """
        print '\b.',
        sys.stdout.flush()

    def start_progressbar(self):
        """
            Method to start progressbar thread
            Args  : None
            Return : None
        """
        self.timer = RepeatingTimer(1.0, self.__show_progressbar)
        self.timer.daemon = True # Allows program to exit if only the thread is alive
        self.timer.start()

    def stop_progressbar(self):
        """
            Method to stop progressbar thread
            Args  : None
            Return : None
        """
        self.timer.cancel()
