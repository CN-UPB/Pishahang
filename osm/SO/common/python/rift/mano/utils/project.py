#!/usr/bin/env python3

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

import abc
import asyncio
import logging
from time import sleep

import gi
gi.require_version('RwProjectManoYang', '1.0')
gi.require_version('RwDts', '1.0')
from gi.repository import (
    RwProjectManoYang,
    RwDts as rwdts,
    ProtobufC,
    RwTypes,
)

import rift.tasklets


class ManoProjectError(Exception):
    pass


class ManoProjNameSetErr(ManoProjectError):
    pass


class ManoProjXpathNoProjErr(ManoProjectError):
    pass


class ManoProjXpathKeyErr(ManoProjectError):
    pass


class ManoProjXpathNotRootErr(ManoProjectError):
    pass


class ManoProjXpathPresentErr(ManoProjectError):
    pass


NS = 'rw-project'
PROJECT = 'project'
NS_PROJECT = '{}:{}'.format(NS, PROJECT)
XPATH = '/{}'.format(NS_PROJECT)
XPATH_LEN = len(XPATH)

NAME = 'name'
NAME_LEN = len(NAME)
NS_NAME = '{}:{}'.format(NS, NAME)

DEFAULT_PROJECT = 'default'
DEFAULT_PREFIX = "{}[{}='{}']".format(XPATH,
                                      NS_NAME,
                                      DEFAULT_PROJECT)


class ManoProject(object):
    '''Class to handle the project name'''

    log = None

    @classmethod
    def instance_from_xpath(cls, xpath, log):
        name = cls.from_xpath(xpath, log)
        if name is None:
            return None

        proj = ManoProject(log, name=name)
        return proj

    @classmethod
    def from_xpath(cls, xpath, log):
        log.debug("Get project name from {}".format(xpath));

        if XPATH in xpath:
            idx = xpath.find(XPATH)
            if idx == -1:
                msg = "Project not found in XPATH: {}".format(xpath)
                log.error(msg)
                raise ManoProjXpathNoProjErr(msg)

            sub = xpath[idx+XPATH_LEN:].strip()
            if (len(sub) < NAME_LEN) or (sub[0] != '['):
                msg = "Project name not found in XPath: {}".format(xpath)
                log.error(msg)
                raise ManoProjXpathKeyErr(msg)

            sub = sub[1:].strip()
            idx = sub.find(NS_NAME)
            if idx == -1:
                idx = sub.find(NAME)
            if idx != 0:
                msg = "Project name not found in XPath: {}".format(xpath)
                log.error(msg)
                raise ManoProjXpathKeyErr(msg)

            idx = sub.find(']')
            if idx == -1:
                msg = "XPath is invalid: {}".format(xpath)
                log.error(msg)
                raise ManoProjXpathKeyErr(msg)

            sub = sub[:idx].strip()
            try:
                log.debug("Key and value found: {}".format(sub))
                k, n = sub.split("=", 2)
                name = n.strip(' \'"')
                if name is None:
                    msg = "Project name is empty in XPath".format(xpath)
                    log.error(msg)
                    raise ManoProjXpathKeyErr (msg)

                log.debug("Found project name {} from XPath {}".
                          format(name, xpath))
                return name

            except ValueError as e:
                msg = "Project name not found in XPath: {}, exception: {}" \
                      .format(xpath, e)
                log.exception(msg)
                raise ManoProjXpathKeyErr(msg)
        else:
                msg = "Project not found in XPATH: {}".format(xpath)
                log.error(msg)
                raise ManoProjXpathNoProjErr(msg)

    @classmethod
    def get_log(cls):
        if not cls.log:
            cls.log = logging.getLogger('rw-mano-log.rw-project')
            cls.log.setLevel(logging.ERROR)

    @classmethod
    def prefix_project(cls, xpath, project=None, log=None):
        if log is None:
            log = cls.get_log()

        if project is None:
            project = DEFAULT_PROJECT
            proj_prefix = DEFAULT_PREFIX
        else:
            proj_prefix = "{}[{}='{}']".format(XPATH,
                                               NS_NAME,
                                               project)

        prefix = ''
        suffix = xpath
        idx = xpath.find('C,/')
        if idx == -1:
            idx = xpath.find('D,/')

        suffix = xpath
        if idx != -1:
            prefix = xpath[:2]
            suffix = xpath[2:]

        if suffix[0] != '/':
            msg = "Non-rooted xpath provided: {}".format(xpath)
            log.error(msg)
            raise ManoProjXpathNotRootErr(msg)

        idx = suffix.find(XPATH)
        if idx == 0:
            name = cls.from_xpath(xpath, log)
            if name == project:
                log.debug("Project already in the XPATH: {}".format(xpath))
                return xpath

            else:
                msg = "Different project {} already in XPATH {}". \
                      format(name, xpath)
                log.error(msg)
                raise ManoProjXpathPresentErr(msg)

        ret = prefix + proj_prefix + suffix
        return ret


    def __init__(self, log, name=None, tasklet=None):
        self._log = log
        self._name = None
        self._prefix = None
        self._pbcm = None
        self._tasklet = None
        self._dts = None
        self._loop = None
        self._log_hdl = None

        # Track if the apply config was received
        self._apply = False

        if name:
            self.name = name

    def update(self, tasklet):
        # Store the commonly used properties from a tasklet
        self._tasklet = tasklet
        self._log_hdl = tasklet.log_hdl
        self._dts = tasklet.dts
        self._loop = tasklet.loop

    @property
    def name(self):
        return self._name

    @property
    def log(self):
        return self._log

    @property
    def prefix(self):
        return self._prefix

    @property
    def pbcm(self):
        return self._pbcm

    @property
    def config(self):
        return self._pbcm.project_config

    @property
    def tasklet(self):
        return self._tasklet

    @property
    def log_hdl(self):
        return self._log_hdl

    @property
    def dts(self):
        return self._dts

    @property
    def loop(self):
        return self._loop

    @name.setter
    def name(self, value):
        if self._name is None:
            self._name = value
            self._prefix = "{}[{}='{}']".format(XPATH,
                                                NS_NAME,
                                                self._name)
            self._pbcm = RwProjectManoYang.YangData_RwProject_Project(
                name=self._name)

        elif self._name == value:
            self._log.debug("Setting the same name again for project {}".
                            format(value))
        else:
            msg = "Project name already set to {}".format(self._name)
            self._log.error(msg)
            raise ManoProjNameSetErr(msg)

    def set_from_xpath(self, xpath):
        self.name = ManoProject.from_xpath(xpath, self._log)

    def add_project(self, xpath):
        return ManoProject.prefix_project(xpath, log=self._log, project=self._name)

    @abc.abstractmethod
    @asyncio.coroutine
    def delete_prepare(self):
        self._log.debug("Delete prepare for project {}".format(self._name))
        return (True, "True")

    @abc.abstractmethod
    @asyncio.coroutine
    def register(self):
        msg = "Register not implemented for project type {}". \
              format(self.__class__.__name__)
        self._log.error(msg)
        raise NotImplementedError(msg)

    @abc.abstractmethod
    def deregister(self):
        msg = "De-register not implemented for project type {}". \
              format(self.__class__.__name__)
        self._log.error(msg)
        raise NotImplementedError(msg)

    def rpc_check(self, msg, xact_info=None):
        '''Check if the rpc is for this project'''
        try:
            project = msg.project_name
        except AttributeError as e:
            project = DEFAULT_PROJECT

        if project != self.name:
            self._log.debug("Project {}: RPC is for different project {}".
                            format(self.name, project))
            if xact_info:
                xact_info.respond_xpath(rwdts.XactRspCode.ACK)
            return False

        return True

    @asyncio.coroutine
    def create_project(self, dts):
        proj_xpath = "C,{}/config".format(self.prefix)
        self._log.info("Creating project: {} with {}".
                       format(proj_xpath, self.config.as_dict()))

        yield from dts.query_create(proj_xpath,
                                    rwdts.XactFlag.ADVISE,
                                    self.config)


def get_add_delete_update_cfgs(dts_member_reg, xact, key_name):
    #TODO: Check why this is getting called during project delete
    if not dts_member_reg:
        return [], [], []

    # Unforunately, it is currently difficult to figure out what has exactly
    # changed in this xact without Pbdelta support (RIFT-4916)
    # As a workaround, we can fetch the pre and post xact elements and
    # perform a comparison to figure out adds/deletes/updates
    xact_cfgs = list(dts_member_reg.get_xact_elements(xact))
    curr_cfgs = list(dts_member_reg.elements)

    xact_key_map = {getattr(cfg, key_name): cfg for cfg in xact_cfgs}
    curr_key_map = {getattr(cfg, key_name): cfg for cfg in curr_cfgs}

    # Find Adds
    added_keys = set(xact_key_map) - set(curr_key_map)
    added_cfgs = [xact_key_map[key] for key in added_keys]

    # Find Deletes
    deleted_keys = set(curr_key_map) - set(xact_key_map)
    deleted_cfgs = [curr_key_map[key] for key in deleted_keys]

    # Find Updates
    updated_keys = set(curr_key_map) & set(xact_key_map)
    updated_cfgs = [xact_key_map[key] for key in updated_keys if xact_key_map[key] != curr_key_map[key]]

    return added_cfgs, deleted_cfgs, updated_cfgs


class ProjectConfigCallbacks(object):
    def __init__(self,
                 on_add_apply=None, on_add_prepare=None,
                 on_delete_apply=None, on_delete_prepare=None):

        @asyncio.coroutine
        def prepare_noop(*args, **kwargs):
            pass

        def apply_noop(*args, **kwargs):
            pass

        self.on_add_apply = on_add_apply
        self.on_add_prepare = on_add_prepare
        self.on_delete_apply = on_delete_apply
        self.on_delete_prepare = on_delete_prepare

        for f in ('on_add_apply', 'on_delete_apply'):
            ref = getattr(self, f)
            if ref is None:
                setattr(self, f, apply_noop)
                continue

            if asyncio.iscoroutinefunction(ref):
                raise ValueError('%s cannot be a coroutine' % (f,))

        for f in ('on_add_prepare', 'on_delete_prepare'):
            ref = getattr(self, f)
            if ref is None:
                setattr(self, f, prepare_noop)
                continue

            if not asyncio.iscoroutinefunction(ref):
                raise ValueError("%s must be a coroutine" % f)


class ProjectDtsHandler(object):
    XPATH = "C,{}/project-config".format(XPATH)

    def __init__(self, dts, log, callbacks, sub_config=True):
        self._dts = dts
        self._log = log
        self._callbacks = callbacks

        if sub_config:
            self.xpath = ProjectDtsHandler.XPATH
            self._key = 'name_ref'
        else:
            self.xpath = "C,{}".format(XPATH)
            self._key = 'name'

        self.reg = None
        self.projects = []

    @property
    def log(self):
        return self._log

    @property
    def dts(self):
        return self._dts

    def add_project(self, name):
        self._log.info("Adding project: {}".format(name))

        if name not in self.projects:
            self._callbacks.on_add_apply(name)
            self.projects.append(name)
        else:
            self._log.error("Project already present: {}".
                           format(name))

    def delete_project(self, name):
        self._log.info("Deleting project: {}".format(name))
        if name in self.projects:
            self._callbacks.on_delete_apply(name)
            self.projects.remove(name)
        else:
            self._log.error("Unrecognized project: {}".
                           format(name))

    def update_project(self, name):
        """ Update an existing project

        Currently, we do not take any action on MANO for this,
        so no callbacks are defined

        Arguments:
            msg - The project config message
        """
        self._log.info("Updating project: {}".format(name))
        if name in self.projects:
            pass
        else:
            self.add_project(name)

    def register(self):
        def on_init(acg, xact, scratch):
            self._log.debug("on_init")
            scratch["projects"] = {
                "added": [],
                "deleted": [],
                "updated": [],
            }
            return scratch

        def readd_projects(xact):
            self._log.info("Re-add projects")

            for cfg, ks in self._reg.get_xact_elements(xact, include_keyspec=True):
                xpath = ks.to_xpath(RwProjectManoYang.get_schema())
                self._log.debug("Got ks {} for cfg {}".format(xpath, cfg.as_dict()))
                name = ManoProject.from_xpath(xpath, self._log)
                self._log.debug("Project to add: {}".format(name))
                self.add_project(name)

        @asyncio.coroutine
        def apply_config(dts, acg, xact, action, scratch):
            self._log.debug("Got project apply config (xact: %s) (action: %s): %s",
                            xact, action, scratch)

            if xact.xact is None:
                if action == rwdts.AppconfAction.INSTALL:
                    readd_projects(xact)
                else:
                    self._log.debug("No xact handle.  Skipping apply config")

                return

            try:
                add_cfgs = scratch["projects"]["added"]
            except KeyError:
                add_cfgs = []

            try:
                del_cfgs = scratch["projects"]["deleted"]
            except KeyError:
                del_cfgs = []

            try:
                update_cfgs = scratch["projects"]["updated"]
            except KeyError:
                update_cfgs = []


            # Handle Deletes
            for name in del_cfgs:
                self.delete_project(name)

            # Handle Adds
            for name, msg in add_cfgs:
                self.add_project(name)

            # Handle Updates
            for name, msg in update_cfgs:
                self.update_project(name)

            try:
                del scratch["projects"]
            except KeyError:
                pass

            return RwTypes.RwStatus.SUCCESS

        @asyncio.coroutine
        def on_prepare(dts, acg, xact, xact_info, ks_path, msg, scratch):
            """ Prepare callback from DTS for Project """

            action = xact_info.query_action
            xpath = ks_path.to_xpath(RwProjectManoYang.get_schema())
            self._log.debug("Project xpath: {}".format(xpath))
            name = ManoProject.from_xpath(xpath, self._log)

            self._log.debug("Project %s on_prepare config received (action: %s): %s",
                            name, xact_info.query_action, msg)

            if action == rwdts.QueryAction.CREATE:
                if name in self.projects:
                    self._log.debug("Project {} already exists. Ignore request".
                                    format(name))
                else:
                    yield from self._callbacks.on_add_prepare(name)
                    scratch["projects"]["added"].append((name, msg))

            elif action == rwdts.QueryAction.UPDATE:
                if name in self.projects:
                    scratch["projects"]["updated"].append((name, msg))
                else:
                    self._log.debug("Project {}: Invoking on_prepare add request".
                                    format(name))
                    yield from self._callbacks.on_add_prepare(name)
                    scratch["projects"]["added"].append((name, msg))


            elif action == rwdts.QueryAction.DELETE:
                # Check if the entire project got deleted
                fref = ProtobufC.FieldReference.alloc()
                fref.goto_whole_message(msg.to_pbcm())
                if fref.is_field_deleted():
                    if name in self.projects:
                        rc, delete_msg = yield from self._callbacks.on_delete_prepare(name)
                        if not rc:
                            self._log.error("Project {} should not be deleted. Reason : {}".
                                            format(name, delete_msg))

                            xact_info.send_error_xpath(RwTypes.RwStatus.FAILURE,
                                           ProjectDtsHandler.XPATH,
                                           delete_msg)

                            xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                            return

                        scratch["projects"]["deleted"].append(name)
                    else:
                        self._log.warning("Delete on unknown project: {}".
                                          format(name))
            else:
                self._log.error("Action (%s) NOT SUPPORTED", action)
                xact_info.respond_xpath(rwdts.XactRspCode.NACK)
                return
            xact_info.respond_xpath(rwdts.XactRspCode.ACK)

        self._log.debug("Registering for project config using xpath: %s",
                        ProjectDtsHandler.XPATH,
                        )

        acg_handler = rift.tasklets.AppConfGroup.Handler(
                        on_apply=apply_config,
                        on_init=on_init)

        with self._dts.appconf_group_create(acg_handler) as acg:
            self._reg = acg.register(
                    xpath=ProjectDtsHandler.XPATH,
                    flags=rwdts.Flag.SUBSCRIBER | rwdts.Flag.DELTA_READY | rwdts.Flag.CACHE,
                    on_prepare=on_prepare,
                    )


class ProjectHandler(object):
    def __init__(self, tasklet, project_class, **kw):
        self._tasklet = tasklet
        self._log = tasklet.log
        self._log_hdl = tasklet.log_hdl
        self._dts = tasklet.dts
        self._loop = tasklet.loop
        self._class = project_class
        self._kw = kw

        self._log.debug("Creating project config handler")
        self.project_cfg_handler = ProjectDtsHandler(
            self._dts, self._log,
            ProjectConfigCallbacks(
                on_add_apply=self.on_project_added,
                on_add_prepare=self.on_add_prepare,
                on_delete_apply=self.on_project_deleted,
                on_delete_prepare=self.on_delete_prepare,
            )
        )

    def _get_tasklet_name(self):
        return self._tasklet.tasklet_info.instance_name

    def _get_project(self, name):
        try:
            proj = self._tasklet.projects[name]
        except Exception as e:
            self._log.exception("Project {} ({})not found for tasklet {}: {}".
                                format(name, list(self._tasklet.projects.keys()),
                                       self._get_tasklet_name(), e))
            raise e

        return proj

    def on_project_deleted(self, name):
        self._log.debug("Project {} deleted".format(name))
        try:
            self._get_project(name).deregister()
        except Exception as e:
            self._log.exception("Project {} deregister for {} failed: {}".
                                format(name, self._get_tasklet_name(), e))

        try:
            proj = self._tasklet.projects.pop(name)
            del proj
        except Exception as e:
            self._log.exception("Project {} delete for {} failed: {}".
                                format(name, self._get_tasklet_name(), e))

    def on_project_added(self, name):
        if name not in self._tasklet.projects:
            try:
                self._tasklet.projects[name] = \
                                self._class(name, self._tasklet, **(self._kw))
                task = asyncio.ensure_future(self._get_project(name).register(),
                                      loop=self._loop)

                self._log.debug("Project {} register: {}".format(name, str(task)))

            except Exception as e:
                self._log.exception("Project {} create for {} failed: {}".
                                    format(name, self._get_tasklet_name(), e))
                raise e

        self._log.debug("Project {} added to tasklet {}".
                        format(name, self._get_tasklet_name()))
        self._get_project(name)._apply = True

    @asyncio.coroutine
    def on_add_prepare(self, name):
        self._log.debug("Project {} to be added to {}".
                        format(name, self._get_tasklet_name()))
        if name in self._tasklet.projects:
            self._log.error("Project {} already exists for {}".
                            format(name, self._get_tasklet_name()))
            return

        try:
            self._tasklet.projects[name] = \
                                self._class(name, self._tasklet, **(self._kw))
            yield from self._get_project(name).register()

        except Exception as e:
            self._log.exception("Project {} create for {} failed: {}".
                                format(name, self._get_tasklet_name(), e))
            raise e

    @asyncio.coroutine
    def on_delete_prepare(self, name):
        self._log.debug("Project {} being deleted for tasklet {}".
                        format(name, self._get_tasklet_name()))
        rc, delete_msg = yield from self._get_project(name).delete_prepare()
        return rc, delete_msg

    def register(self):
        self.project_cfg_handler.register()
