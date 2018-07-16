"""
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

@file operations.py
@author Varun Prasad(varun.prasad@riftio.com)
@date 2016-06-14
"""

import daemon
import daemon.pidfile
import os
import signal
import subprocess
import sys
import time

import gi
gi.require_version('RwcalYang', '1.0')
gi.require_version('RwCal', '1.0')
gi.require_version('RwLog', '1.0')

from . import server as cal_server
import rift.cal.utils as cal_util
import rift.rwcal.cloudsim.shell as shell



class CloudsimServerOperations(cal_util.CloudSimCalMixin):
    """Convenience class to provide start, stop and cleanup operations
    
    Attributes:
        log (logging): Log instance
        PID_FILE (str): Location to generate the PID file.
    """
    PID_FILE = "/var/log/rift/cloudsim_server.pid"

    def __init__(self, log):
        super().__init__()
        self.log = log

    @property
    def pid(self):
        pid = None
        try:
            with open(self.PID_FILE) as fh:
                pid = fh.readlines()[0]
                pid = int(pid.strip())
        except IndexError:
            self.log.error("Looks like the pid file does not contain a valid ID")
        except OSError:
            self.log.debug("No PID file found.")

        return pid

    def is_pid_exists(self, pid):
        try:
            os.kill(pid, 0)
        except OSError:
            return False

        return True

    def start_server(self, foreground=False):
        """Start the tornado app """

        # Before starting verify if all requirements are satisfied
        cal_server.CalServer.verify_requirements(self.log)

        # If the /var/log directory is not present, then create it first.
        if not os.path.exists(os.path.dirname(self.PID_FILE)):
            self.log.warning("Creating /var/log/rift directory for log storage")
            os.makedirs(os.path.dirname(self.PID_FILE))

        # Check if an exiting PID file is present, if so check if it has an
        # associated proc, otherwise it's a zombie file so clean it.
        # Otherwise the daemon fails silently.
        if self.pid is not None and not self.is_pid_exists(self.pid):
            self.log.warning("Removing stale PID file")
            os.remove(self.PID_FILE)



        def start(daemon_mode=False):

            log = cal_util.Logger(daemon_mode=daemon_mode, log_name='')
            log.logger.info("Starting the cloud server.")
            server = cal_server.CalServer()
            server.start()

        if foreground:
            # Write the PID file for consistency
            with open(self.PID_FILE, mode='w') as fh:
                fh.write(str(os.getpid()) + "\n")
            start()
        else:
            context = daemon.DaemonContext(
                pidfile=daemon.pidfile.PIDLockFile(self.PID_FILE))
            with context:
                start(daemon_mode=True)

    def stop_server(self):
        """Stop the daemon"""

        def kill_pid(pid, sig):
            self.log.info("Sending {} to PID: {}".format(str(sig), pid))
            os.kill(pid, sig)


        def search_and_kill():
            """In case the PID file is not found, and the server is still
            running, as a last resort we search thro' the process table
            and stop the server."""
            cmd = ["pgrep", "-u", "daemon,root", "python3"]

            try:
               pids = subprocess.check_output(cmd)
            except subprocess.CalledProcessError:
                self.log.error("No Cloudsim server process found. "
                        "Please ensure Cloudsim server is running")
                return

            pids = map(int, pids.split())

            for pid in pids:
                if pid != os.getpid():
                    kill_sequence(pid)

        def wait_till_exit(pid, timeout=30, retry_interval=1):
            start_time = time.time()

            while True:
                if not self.is_pid_exists(pid):
                    msg = "Killed {}".format(pid)
                    print (msg)
                    return True

                time_elapsed = time.time() - start_time
                time_remaining = timeout - time_elapsed

                self.log.info("Process still exists, trying again in {} sec(s)"
                    .format(retry_interval))

                if time_remaining <= 0:
                    msg = 'Process {} has not yet terminated within {} secs. Trying SIGKILL'
                    self.log.error(msg.format(pid, timeout))
                    return False

                time.sleep(min(time_remaining, retry_interval))

        def kill_sequence(pid):
            kill_pid(pid, signal.SIGHUP)
            wait_till_exit(pid, timeout=10, retry_interval=2)
            kill_pid(pid, signal.SIGKILL)
            status = wait_till_exit(pid)

            if status:
                # Remove the lock file.
                shell.command("rm -f {}".format(self.PID_FILE))

        pid = self.pid
        if pid is not None:
            self.log.warning("Server running with PID: {} found, "
                             "trying to stop it".format(pid))
            kill_sequence(pid)
        else:
            self.log.warning("No PID file found. Searching the process "
                            "table to find PID")
            search_and_kill()

    def clean_server(self, images=False):
        """Clean all resource using rest APIs. """

        # Delete VDUs
        _, vdus = self.cal.get_vdu_list(self.account)
        for vdu in vdus.vdu_info_list:
            self.cal.delete_vdu(self.account, vdu.vdu_id)

        # Delete Vlinks
        _, vlinks = self.cal.get_virtual_link_list(self.account)
        for vlink in vlinks.virtual_link_info_list:
            self.cal.delete_virtual_link(self.account, vlink.virtual_link_id)

        if images:
            _, images = self.cal.get_image_list(self.account)
            for image in images.image_info_list:
                self.cal.delete_image(self.account, image.id)
