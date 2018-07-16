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

import gi

import rift.downloader as downloader
from gi.repository import RwPkgMgmtYang


TaskStatus = RwPkgMgmtYang.TaskStatus


class PackageFileDownloader(downloader.UrlDownloader):
    STATUS_MAP = {
        downloader.DownloadStatus.STARTED: TaskStatus.QUEUED.value_nick.upper(),
        downloader.DownloadStatus.IN_PROGRESS: TaskStatus.IN_PROGRESS.value_nick.upper(),
        downloader.DownloadStatus.COMPLETED: TaskStatus.COMPLETED.value_nick.upper(),
        downloader.DownloadStatus.FAILED: TaskStatus.FAILED.value_nick.upper(),
        downloader.DownloadStatus.CANCELLED: TaskStatus.CANCELLED.value_nick.upper()
        }

    @classmethod
    def from_rpc_input(cls, rpc_input, file_obj, proxy, log=None, auth=None, project=None):
        """Convenience class to set up an instance form RPC data
        """
        url_downloader = cls(
            rpc_input.external_url,
            rpc_input.package_id,
            rpc_input.package_path,
            rpc_input.package_type,
            rpc_input.vnfd_file_type, 
            rpc_input.nsd_file_type,
            auth=auth,
            proxy=proxy,
            file_obj=file_obj,
            log=log,
            project=project)

        return url_downloader

    def __init__(self,
                 url,
                 package_id,
                 package_path,
                 package_type,
                 vnfd_file_type, 
                 nsd_file_type,
                 proxy,
                 file_obj=None,
                 delete_on_fail=True,
                 decompress_on_fly=False,
                 auth=None,
                 log=None,
                 project=None):
        super().__init__(
                url,
                file_obj=file_obj,
                delete_on_fail=delete_on_fail,
                decompress_on_fly=decompress_on_fly,
                auth=auth,
                log=log)

        self.package_id = package_id
        self.package_type = package_type
        self.package_path = package_path
        self.package_file_type = vnfd_file_type.lower() \
                if package_type == 'VNFD' else nsd_file_type.lower()
        self.proxy = proxy
        self.project = project

    def convert_to_yang(self):

        job = RwPkgMgmtYang.YangData_RwProject_Project_DownloadJobs_Job.from_dict({
                "url": self.meta.url,
                "download_id": self.meta.download_id,
                "package_id": self.package_id,
                "package_path": self.package_path,
                "package_type": self.package_type,
                "detail": self.meta.detail,
                "progress_percent": self.meta.progress_percent,
                "bytes_downloaded": self.meta.bytes_downloaded,
                "bytes_total": self.meta.bytes_total,
                "bytes_per_second": self.meta.bytes_per_second,
                "start_time": self.meta.start_time,
                "stop_time": self.meta.stop_time,
                "status": self.STATUS_MAP[self.meta.status]
            })

        return job

    # Start of delegate calls
    def call_delegate(self, event):
        if not self.delegate:
            return

        job = self.convert_to_yang()
        getattr(self.delegate, event)(job)


    def download_succeeded(self):

        try:
            # Add the file to package
            self.proxy.package_file_add(
                self.meta.filepath,
                self.package_type,
                self.package_id,
                self.package_path, 
                self.package_file_type,
                self.project)

        except Exception as e:
            self.log.exception(e)
            self.meta.detail = str(e)
            self.download_failed()
            return

        super().download_succeeded()

