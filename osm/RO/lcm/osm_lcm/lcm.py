#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio
import yaml
import ROclient
import dbmemory
import dbmongo
import fslocal
import msglocal
import msgkafka
import logging
import functools
import sys
from dbbase import DbException
from fsbase import FsException
from msgbase import MsgException
from os import environ
# from vca import DeployApplication, RemoveApplication
from n2vc.vnf import N2VC
# import os.path
# import time

from copy import deepcopy
from http import HTTPStatus
from time import time


class LcmException(Exception):
    pass


class Lcm:

    def __init__(self, config_file):
        """
        Init, Connect to database, filesystem storage, and messaging
        :param config: two level dictionary with configuration. Top level should contain 'database', 'storage',
        :return: None
        """

        self.db = None
        self.msg = None
        self.fs = None
        self.pings_not_received = 1

        # contains created tasks/futures to be able to cancel
        self.lcm_ns_tasks = {}
        self.lcm_vim_tasks = {}
        self.lcm_sdn_tasks = {}
        # logging
        self.logger = logging.getLogger('lcm')
        # load configuration
        config = self.read_config_file(config_file)
        self.config = config
        self.ro_config={
            "endpoint_url": "http://{}:{}/openmano".format(config["RO"]["host"], config["RO"]["port"]),
            "tenant":  config.get("tenant", "osm"),
            "logger_name": "lcm.ROclient",
            "loglevel": "ERROR",
        }

        self.vca = config["VCA"]  # TODO VCA
        self.loop = None

        # logging
        log_format_simple = "%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s"
        log_formatter_simple = logging.Formatter(log_format_simple, datefmt='%Y-%m-%dT%H:%M:%S')
        config["database"]["logger_name"] = "lcm.db"
        config["storage"]["logger_name"] = "lcm.fs"
        config["message"]["logger_name"] = "lcm.msg"
        if "logfile" in config["global"]:
            file_handler = logging.handlers.RotatingFileHandler(config["global"]["logfile"],
                                                                maxBytes=100e6, backupCount=9, delay=0)
            file_handler.setFormatter(log_formatter_simple)
            self.logger.addHandler(file_handler)
        else:
            str_handler = logging.StreamHandler()
            str_handler.setFormatter(log_formatter_simple)
            self.logger.addHandler(str_handler)

        if config["global"].get("loglevel"):
            self.logger.setLevel(config["global"]["loglevel"])

        # logging other modules
        for k1, logname in {"message": "lcm.msg", "database": "lcm.db", "storage": "lcm.fs"}.items():
            config[k1]["logger_name"] = logname
            logger_module = logging.getLogger(logname)
            if "logfile" in config[k1]:
                file_handler = logging.handlers.RotatingFileHandler(config[k1]["logfile"],
                                                                    maxBytes=100e6, backupCount=9, delay=0)
                file_handler.setFormatter(log_formatter_simple)
                logger_module.addHandler(file_handler)
            if "loglevel" in config[k1]:
                logger_module.setLevel(config[k1]["loglevel"])

        self.n2vc = N2VC(
            log=self.logger,
            server=config['VCA']['host'],
            port=config['VCA']['port'],
            user=config['VCA']['user'],
            secret=config['VCA']['secret'],
            # TODO: This should point to the base folder where charms are stored,
            # if there is a common one (like object storage). Otherwise, leave
            # it unset and pass it via DeployCharms
            # artifacts=config['VCA'][''],
            artifacts=None,
        )

        try:
            if config["database"]["driver"] == "mongo":
                self.db = dbmongo.DbMongo()
                self.db.db_connect(config["database"])
            elif config["database"]["driver"] == "memory":
                self.db = dbmemory.DbMemory()
                self.db.db_connect(config["database"])
            else:
                raise LcmException("Invalid configuration param '{}' at '[database]':'driver'".format(
                    config["database"]["driver"]))

            if config["storage"]["driver"] == "local":
                self.fs = fslocal.FsLocal()
                self.fs.fs_connect(config["storage"])
            else:
                raise LcmException("Invalid configuration param '{}' at '[storage]':'driver'".format(
                    config["storage"]["driver"]))

            if config["message"]["driver"] == "local":
                self.msg = msglocal.MsgLocal()
                self.msg.connect(config["message"])
            elif config["message"]["driver"] == "kafka":
                self.msg = msgkafka.MsgKafka()
                self.msg.connect(config["message"])
            else:
                raise LcmException("Invalid configuration param '{}' at '[message]':'driver'".format(
                    config["storage"]["driver"]))
        except (DbException, FsException, MsgException) as e:
            self.logger.critical(str(e), exc_info=True)
            raise LcmException(str(e))

    def update_db(self, item, _id, _desc):
        try:
            self.db.replace(item, _id, _desc)
        except DbException as e:
            self.logger.error("Updating {} _id={}: {}".format(item, _id, e))

    def update_db_2(self, item, _id, _desc):
        try:
            self.db.set_one(item, {"_id": _id}, _desc)
        except DbException as e:
            self.logger.error("Updating {} _id={}: {}".format(item, _id, e))

    async def vim_create(self, vim_content, order_id):
        vim_id = vim_content["_id"]
        logging_text = "Task vim_create={} ".format(vim_id)
        self.logger.debug(logging_text + "Enter")
        db_vim = None
        exc = None
        try:
            step = "Getting vim from db"
            db_vim = self.db.get_one("vims", {"_id": vim_id})
            if "_admin" not in db_vim:
                db_vim["_admin"] = {}
            if "deployed" not in db_vim["_admin"]:
                db_vim["_admin"]["deployed"] = {}
            db_vim["_admin"]["deployed"]["RO"] = None

            step = "Creating vim at RO"
            RO = ROclient.ROClient(self.loop, **self.ro_config)
            vim_RO = deepcopy(vim_content)
            vim_RO.pop("_id", None)
            vim_RO.pop("_admin", None)
            vim_RO.pop("schema_version", None)
            vim_RO.pop("schema_type", None)
            vim_RO.pop("vim_tenant_name", None)
            vim_RO["type"] = vim_RO.pop("vim_type")
            vim_RO.pop("vim_user", None)
            vim_RO.pop("vim_password", None)
            desc = await RO.create("vim", descriptor=vim_RO)
            RO_vim_id = desc["uuid"]
            db_vim["_admin"]["deployed"]["RO"] = RO_vim_id
            self.update_db("vims", vim_id, db_vim)

            step = "Attach vim to RO tenant"
            vim_RO = {"vim_tenant_name": vim_content["vim_tenant_name"],
                "vim_username": vim_content["vim_user"],
                "vim_password": vim_content["vim_password"],
                "config": vim_content["config"]
            }
            desc = await RO.attach_datacenter(RO_vim_id , descriptor=vim_RO)
            db_vim["_admin"]["operationalState"] = "ENABLED"
            self.update_db("vims", vim_id, db_vim)

            self.logger.debug(logging_text + "Exit Ok RO_vim_id".format(RO_vim_id))
            return RO_vim_id

        except (ROclient.ROClientException, DbException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {}".format(e), exc_info=True)
            exc = e
        finally:
            if exc and db_vim:
                db_vim["_admin"]["operationalState"] = "ERROR"
                db_vim["_admin"]["detailed-status"] = "ERROR {}: {}".format(step , exc)
                self.update_db("vims", vim_id, db_vim)

    async def vim_edit(self, vim_content, order_id):
        vim_id = vim_content["_id"]
        logging_text = "Task vim_edit={} ".format(vim_id)
        self.logger.debug(logging_text + "Enter")
        db_vim = None
        exc = None
        step = "Getting vim from db"
        try:
            db_vim = self.db.get_one("vims", {"_id": vim_id})
            if db_vim.get("_admin") and db_vim["_admin"].get("deployed") and db_vim["_admin"]["deployed"].get("RO"):
                RO_vim_id = db_vim["_admin"]["deployed"]["RO"]
                step = "Editing vim at RO"
                RO = ROclient.ROClient(self.loop, **self.ro_config)
                vim_RO = deepcopy(vim_content)
                vim_RO.pop("_id", None)
                vim_RO.pop("_admin", None)
                vim_RO.pop("schema_version", None)
                vim_RO.pop("schema_type", None)
                vim_RO.pop("vim_tenant_name", None)
                vim_RO["type"] = vim_RO.pop("vim_type")
                vim_RO.pop("vim_user", None)
                vim_RO.pop("vim_password", None)
                if vim_RO:
                    desc = await RO.edit("vim", RO_vim_id, descriptor=vim_RO)

                step = "Editing vim-account at RO tenant"
                vim_RO = {}
                for k in ("vim_tenant_name", "vim_password", "config"):
                    if k in vim_content:
                        vim_RO[k] = vim_content[k]
                if "vim_user" in vim_content:
                    vim_content["vim_username"] = vim_content["vim_user"]
                if vim_RO:
                    desc = await RO.edit("vim_account", RO_vim_id, descriptor=vim_RO)
                db_vim["_admin"]["operationalState"] = "ENABLED"
                self.update_db("vims", vim_id, db_vim)

            self.logger.debug(logging_text + "Exit Ok RO_vim_id".format(RO_vim_id))
            return RO_vim_id

        except (ROclient.ROClientException, DbException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {}".format(e), exc_info=True)
            exc = e
        finally:
            if exc and db_vim:
                db_vim["_admin"]["operationalState"] = "ERROR"
                db_vim["_admin"]["detailed-status"] = "ERROR {}: {}".format(step , exc)
                self.update_db("vims", vim_id, db_vim)

    async def vim_delete(self, vim_id, order_id):
        logging_text = "Task vim_delete={} ".format(vim_id)
        self.logger.debug(logging_text + "Enter")
        db_vim = None
        exc = None
        step = "Getting vim from db"
        try:
            db_vim = self.db.get_one("vims", {"_id": vim_id})
            if db_vim.get("_admin") and db_vim["_admin"].get("deployed") and db_vim["_admin"]["deployed"].get("RO"):
                RO_vim_id = db_vim["_admin"]["deployed"]["RO"]
                RO = ROclient.ROClient(self.loop, **self.ro_config)
                step = "Detaching vim from RO tenant"
                try:
                    await RO.detach_datacenter(RO_vim_id)
                except ROclient.ROClientException as e:
                    if e.http_code == 404:  # not found
                        self.logger.debug(logging_text + "RO_vim_id={} already detached".format(RO_vim_id))
                    else:
                        raise

                step = "Deleting vim from RO"
                try:
                    await RO.delete("vim", RO_vim_id)
                except ROclient.ROClientException as e:
                    if e.http_code == 404:  # not found
                        self.logger.debug(logging_text + "RO_vim_id={} already deleted".format(RO_vim_id))
                    else:
                        raise
            else:
                # nothing to delete
                self.logger.error(logging_text + "Skipping. There is not RO information at database")
            self.db.del_one("vims", {"_id": vim_id})
            self.logger.debug("vim_delete task vim_id={} Exit Ok".format(vim_id))
            return None

        except (ROclient.ROClientException, DbException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {}".format(e), exc_info=True)
            exc = e
        finally:
            if exc and db_vim:
                db_vim["_admin"]["operationalState"] = "ERROR"
                db_vim["_admin"]["detailed-status"] = "ERROR {}: {}".format(step , exc)
                self.update_db("vims", vim_id, db_vim)

    async def sdn_create(self, sdn_content, order_id):
        sdn_id = sdn_content["_id"]
        logging_text = "Task sdn_create={} ".format(sdn_id)
        self.logger.debug(logging_text + "Enter")
        db_sdn = None
        exc = None
        try:
            step = "Getting sdn from db"
            db_sdn = self.db.get_one("sdns", {"_id": sdn_id})
            if "_admin" not in db_sdn:
                db_sdn["_admin"] = {}
            if "deployed" not in db_sdn["_admin"]:
                db_sdn["_admin"]["deployed"] = {}
            db_sdn["_admin"]["deployed"]["RO"] =  None

            step = "Creating sdn at RO"
            RO = ROclient.ROClient(self.loop, **self.ro_config)
            sdn_RO = deepcopy(sdn_content)
            sdn_RO.pop("_id", None)
            sdn_RO.pop("_admin", None)
            sdn_RO.pop("schema_version", None)
            sdn_RO.pop("schema_type", None)
            desc = await RO.create("sdn", descriptor=sdn_RO)
            RO_sdn_id = desc["uuid"]
            db_sdn["_admin"]["deployed"]["RO"] = RO_sdn_id
            db_sdn["_admin"]["operationalState"] = "ENABLED"
            self.update_db("sdns", sdn_id, db_sdn)
            self.logger.debug(logging_text + "Exit Ok RO_sdn_id".format(RO_sdn_id))
            return RO_sdn_id

        except (ROclient.ROClientException, DbException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {}".format(e), exc_info=True)
            exc = e
        finally:
            if exc and db_sdn:
                db_sdn["_admin"]["operationalState"] = "ERROR"
                db_sdn["_admin"]["detailed-status"] = "ERROR {}: {}".format(step , exc)
                self.update_db("sdns", sdn_id, db_sdn)

    async def sdn_edit(self, sdn_content, order_id):
        sdn_id = sdn_content["_id"]
        logging_text = "Task sdn_edit={} ".format(sdn_id)
        self.logger.debug(logging_text + "Enter")
        db_sdn = None
        exc = None
        step = "Getting sdn from db"
        try:
            db_sdn = self.db.get_one("sdns", {"_id": sdn_id})
            if db_sdn.get("_admin") and db_sdn["_admin"].get("deployed") and db_sdn["_admin"]["deployed"].get("RO"):
                RO_sdn_id = db_sdn["_admin"]["deployed"]["RO"]
                RO = ROclient.ROClient(self.loop, **self.ro_config)
                step = "Editing sdn at RO"
                sdn_RO = deepcopy(sdn_content)
                sdn_RO.pop("_id", None)
                sdn_RO.pop("_admin", None)
                sdn_RO.pop("schema_version", None)
                sdn_RO.pop("schema_type", None)
                if sdn_RO:
                    desc = await RO.edit("sdn", RO_sdn_id, descriptor=sdn_RO)
                db_sdn["_admin"]["operationalState"] = "ENABLED"
                self.update_db("sdns", sdn_id, db_sdn)

            self.logger.debug(logging_text + "Exit Ok RO_sdn_id".format(RO_sdn_id))
            return RO_sdn_id

        except (ROclient.ROClientException, DbException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {}".format(e), exc_info=True)
            exc = e
        finally:
            if exc and db_sdn:
                db_sdn["_admin"]["operationalState"] = "ERROR"
                db_sdn["_admin"]["detailed-status"] = "ERROR {}: {}".format(step , exc)
                self.update_db("sdns", sdn_id, db_sdn)

    async def sdn_delete(self, sdn_id, order_id):
        logging_text = "Task sdn_delete={} ".format(sdn_id)
        self.logger.debug(logging_text + "Enter")
        db_sdn = None
        exc = None
        step = "Getting sdn from db"
        try:
            db_sdn = self.db.get_one("sdns", {"_id": sdn_id})
            if db_sdn.get("_admin") and db_sdn["_admin"].get("deployed") and db_sdn["_admin"]["deployed"].get("RO"):
                RO_sdn_id = db_sdn["_admin"]["deployed"]["RO"]
                RO = ROclient.ROClient(self.loop, **self.ro_config)
                step = "Deleting sdn from RO"
                try:
                    await RO.delete("sdn", RO_sdn_id)
                except ROclient.ROClientException as e:
                    if e.http_code == 404:  # not found
                        self.logger.debug(logging_text + "RO_sdn_id={} already deleted".format(RO_sdn_id))
                    else:
                        raise
            else:
                # nothing to delete
                self.logger.error(logging_text + "Skipping. There is not RO information at database")
            self.db.del_one("sdns", {"_id": sdn_id})
            self.logger.debug("sdn_delete task sdn_id={} Exit Ok".format(sdn_id))
            return None

        except (ROclient.ROClientException, DbException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {}".format(e), exc_info=True)
            exc = e
        finally:
            if exc and db_sdn:
                db_sdn["_admin"]["operationalState"] = "ERROR"
                db_sdn["_admin"]["detailed-status"] = "ERROR {}: {}".format(step , exc)
                self.update_db("sdns", sdn_id, db_sdn)

    def vnfd2RO(self, vnfd, new_id=None):
        """
        Converts creates a new vnfd descriptor for RO base on input OSM IM vnfd
        :param vnfd: input vnfd
        :param new_id: overrides vnf id if provided
        :return: copy of vnfd
        """
        ci_file = None
        try:
            vnfd_RO = deepcopy(vnfd)
            vnfd_RO.pop("_id", None)
            vnfd_RO.pop("_admin", None)
            if new_id:
                vnfd_RO["id"] = new_id
            for vdu in vnfd_RO["vdu"]:
                if "cloud-init-file" in vdu:
                    base_folder = vnfd["_admin"]["storage"]
                    clout_init_file = "{}/{}/cloud_init/{}".format(
                        base_folder["folder"],
                        base_folder["pkg-dir"],
                        vdu["cloud-init-file"]
                    )
                    ci_file = self.fs.file_open(clout_init_file, "r")
                    # TODO: detect if binary or text. Propose to read as binary and try to decode to utf8. If fails convert to base 64 or similar
                    clout_init_content = ci_file.read()
                    ci_file.close()
                    ci_file = None
                    vdu.pop("cloud-init-file", None)
                    vdu["cloud-init"] = clout_init_content
            return vnfd_RO
        except FsException as e:
            raise LcmException("Error reading file at vnfd {}: {} ".format(vnfd["_id"], e))
        finally:
            if ci_file:
                ci_file.close()

    def n2vc_callback(self, model_name, application_name, workload_status, db_nsr, db_nslcmop, vnf_member_index, task=None):
        """Update the lcm database with the status of the charm.

        Updates the VNF's operational status with the state of the charm:
        - blocked: The unit needs manual intervention
        - maintenance: The unit is actively deploying/configuring
        - waiting: The unit is waiting for another charm to be ready
        - active: The unit is deployed, configured, and ready
        - error: The charm has failed and needs attention.
        - terminated: The charm has been destroyed
        - removing,
        - removed

        Updates the network service's config-status to reflect the state of all
        charms.
        """
        nsr_id = None
        nslcmop_id = None
        update_nsr = update_nslcmop = False
        try:
            nsr_id = db_nsr["_id"]
            nslcmop_id = db_nslcmop["_id"]
            nsr_lcm = db_nsr["_admin"]["deployed"]
            ns_action = db_nslcmop["lcmOperationType"]
            logging_text = "Task ns={} {}={} [n2vc_callback] vnf_index={}".format(nsr_id, ns_action, nslcmop_id,
                                                                                  vnf_member_index)

            if task:
                if task.cancelled():
                    self.logger.debug(logging_text + " task Cancelled")
                    # TODO update db_nslcmop
                    return

                if task.done():
                    exc = task.exception()
                    if exc:
                        self.logger.error(logging_text + " task Exception={}".format(exc))
                        if ns_action in ("instantiate", "terminate"):
                            nsr_lcm["VCA"][vnf_member_index]['operational-status'] = "error"
                            nsr_lcm["VCA"][vnf_member_index]['detailed-status'] = str(exc)
                        elif ns_action == "action":
                            db_nslcmop["operationState"] = "FAILED"
                            db_nslcmop["detailedStatus"] = str(exc)
                            db_nslcmop["statusEnteredTime"] = time()
                            update_nslcmop = True
                            return

                    else:
                        self.logger.debug(logging_text + " task Done")
                        # TODO revise with Adam if action is finished and ok when task is done
                        if ns_action == "action":
                            db_nslcmop["operationState"] = "COMPLETED"
                            db_nslcmop["detailedStatus"] = "Done"
                            db_nslcmop["statusEnteredTime"] = time()
                            update_nslcmop = True
                        # task is Done, but callback is still ongoing. So ignore
                        return
            elif workload_status:
                self.logger.debug(logging_text + " Enter workload_status={}".format(workload_status))
                if nsr_lcm["VCA"][vnf_member_index]['operational-status'] == workload_status:
                    return  # same status, ignore
                nsr_lcm["VCA"][vnf_member_index]['operational-status'] = workload_status
                # TODO N2VC some error message in case of error should be obtained from N2VC
                nsr_lcm["VCA"][vnf_member_index]['detailed-status'] = ""
            else:
                self.logger.critical(logging_text + " Enter with bad parameters", exc_info=True)
                return

            some_failed = False
            all_active = True
            status_map = {}
            for vnf_index, vca_info in nsr_lcm["VCA"].items():
                vca_status = vca_info["operational-status"]
                if vca_status not in status_map:
                    # Initialize it
                    status_map[vca_status] = 0
                status_map[vca_status] += 1

                if vca_status != "active":
                    all_active = False
                if vca_status == "error":
                    some_failed = True
                    db_nsr["config-status"] = "failed"
                    error_text = "fail configuring vnf_index={} {}".format(vnf_member_index,
                                                                           vca_info["detailed-status"])
                    db_nsr["detailed-status"] = error_text
                    db_nslcmop["operationState"] = "FAILED_TEMP"
                    db_nslcmop["detailedStatus"] = error_text
                    db_nslcmop["statusEnteredTime"] = time()
                    break

            if all_active:
                self.logger.debug("[n2vc_callback] ns_instantiate={} vnf_index={} All active".format(nsr_id, vnf_member_index))
                db_nsr["config-status"] = "configured"
                db_nsr["detailed-status"] = "done"
                db_nslcmop["operationState"] = "COMPLETED"
                db_nslcmop["detailedStatus"] = "Done"
                db_nslcmop["statusEnteredTime"] = time()
            elif some_failed:
                pass
            else:
                cs = "configuring: "
                separator = ""
                for status, num in status_map.items():
                    cs += separator + "{}: {}".format(status, num)
                    separator = ", "
                db_nsr["config-status"] = cs
                db_nslcmop["detailedStatus"] = cs
            update_nsr = update_nslcmop = True

        except Exception as e:
            self.logger.critical("[n2vc_callback] vnf_index={} Exception {}".format(vnf_member_index, e), exc_info=True)
        finally:
            try:
                if update_nslcmop:
                    self.update_db("nslcmops", nslcmop_id, db_nslcmop)
                if update_nsr:
                    self.update_db("nsrs", nsr_id, db_nsr)
            except Exception as e:
                self.logger.critical("[n2vc_callback] vnf_index={} Update database Exception {}".format(
                    vnf_member_index, e), exc_info=True)

    async def ns_instantiate(self, nsr_id, nslcmop_id):
        logging_text = "Task ns={} instantiate={} ".format(nsr_id, nslcmop_id)
        self.logger.debug(logging_text + "Enter")
        # get all needed from database
        db_nsr = None
        db_nslcmop = None
        exc = None
        step = "Getting nsr, nslcmop, RO_vims from db"
        try:
            db_nslcmop = self.db.get_one("nslcmops", {"_id": nslcmop_id})
            db_nsr = self.db.get_one("nsrs", {"_id": nsr_id})
            nsd = db_nsr["nsd"]
            nsr_name = db_nsr["name"]   # TODO short-name??

            db_vim = self.db.get_one("vims", {"_id": db_nsr["datacenter"]})
            # if db_vim["_admin"]["operationalState"] == "PROCESSING":
            #     #TODO check if VIM is creating and wait
            if db_vim["_admin"]["operationalState"] != "ENABLED":
                raise LcmException("VIM={} is not available. operationalSstatus={}".format(
                    db_nsr["datacenter"], db_vim["_admin"]["operationalState"]))
            RO_vim_id = db_vim["_admin"]["deployed"]["RO"]

            needed_vnfd = {}
            for c_vnf in nsd["constituent-vnfd"]:
                vnfd_id = c_vnf["vnfd-id-ref"]
                if vnfd_id not in needed_vnfd:
                    step = "Getting vnfd={} from db".format(vnfd_id)
                    needed_vnfd[vnfd_id] = self.db.get_one("vnfds", {"id": vnfd_id})

            nsr_lcm = db_nsr["_admin"].get("deployed")
            if not nsr_lcm:
                nsr_lcm = db_nsr["_admin"]["deployed"] = {
                    "id": nsr_id,
                    "RO": {"vnfd_id": {}, "nsd_id": None, "nsr_id": None, "nsr_status": "SCHEDULED"},
                    "nsr_ip": {},
                    "VCA": {},
                }
            db_nsr["detailed-status"] = "creating"
            db_nsr["operational-status"] = "init"

            deloyment_timeout = 120

            RO = ROclient.ROClient(self.loop, datacenter=RO_vim_id, **self.ro_config)

            # get vnfds, instantiate at RO
            for vnfd_id, vnfd in needed_vnfd.items():
                step = db_nsr["detailed-status"] = "Creating vnfd={} at RO".format(vnfd_id)
                self.logger.debug(logging_text + step)
                vnfd_id_RO = nsr_id + "." + vnfd_id[:200]

                # look if present
                vnfd_list = await RO.get_list("vnfd", filter_by={"osm_id": vnfd_id_RO})
                if vnfd_list:
                    nsr_lcm["RO"]["vnfd_id"][vnfd_id] = vnfd_list[0]["uuid"]
                    self.logger.debug(logging_text + "RO vnfd={} exist. Using RO_id={}".format(
                        vnfd_id, vnfd_list[0]["uuid"]))
                else:
                    vnfd_RO = self.vnfd2RO(vnfd, vnfd_id_RO)
                    desc = await RO.create("vnfd", descriptor=vnfd_RO)
                    nsr_lcm["RO"]["vnfd_id"][vnfd_id] = desc["uuid"]
                    db_nsr["_admin"]["nsState"] = "INSTANTIATED"
                self.update_db("nsrs", nsr_id, db_nsr)

            # create nsd at RO
            nsd_id = nsd["id"]
            step = db_nsr["detailed-status"] = "Creating nsd={} at RO".format(nsd_id)
            self.logger.debug(logging_text + step)

            nsd_id_RO = nsd_id + "." + nsd_id[:200]
            nsd_list = await RO.get_list("nsd", filter_by={"osm_id": nsd_id_RO})
            if nsd_list:
                nsr_lcm["RO"]["nsd_id"] = nsd_list[0]["uuid"]
                self.logger.debug(logging_text + "RO nsd={} exist. Using RO_id={}".format(
                    nsd_id, nsd_list[0]["uuid"]))
            else:
                nsd_RO = deepcopy(nsd)
                nsd_RO["id"] = nsd_id_RO
                nsd_RO.pop("_id", None)
                nsd_RO.pop("_admin", None)
                for c_vnf in nsd_RO["constituent-vnfd"]:
                    vnfd_id = c_vnf["vnfd-id-ref"]
                    c_vnf["vnfd-id-ref"] = nsr_id + "." + vnfd_id[:200]
                desc = await RO.create("nsd", descriptor=nsd_RO)
                db_nsr["_admin"]["nsState"] = "INSTANTIATED"
                nsr_lcm["RO"]["nsd_id"] = desc["uuid"]
            self.update_db("nsrs", nsr_id, db_nsr)

            # Crate ns at RO
            # if present use it unless in error status
            RO_nsr_id = nsr_lcm["RO"].get("nsr_id")
            if RO_nsr_id:
                try:
                    step = db_nsr["detailed-status"] = "Looking for existing ns at RO"
                    self.logger.debug(logging_text + step + " RO_ns_id={}".format(RO_nsr_id))
                    desc = await RO.show("ns", RO_nsr_id)
                except ROclient.ROClientException as e:
                    if e.http_code != HTTPStatus.NOT_FOUND:
                        raise
                    RO_nsr_id = nsr_lcm["RO"]["nsr_id"] = None
                if RO_nsr_id:
                    ns_status, ns_status_info = RO.check_ns_status(desc)
                    nsr_lcm["RO"]["nsr_status"] = ns_status
                    if ns_status == "ERROR":
                        step = db_nsr["detailed-status"] = "Deleting ns at RO"
                        self.logger.debug(logging_text + step + " RO_ns_id={}".format(RO_nsr_id))
                        await RO.delete("ns", RO_nsr_id)
                        RO_nsr_id = nsr_lcm["RO"]["nsr_id"] = None

            if not RO_nsr_id:
                step = db_nsr["detailed-status"] = "Creating ns at RO"
                self.logger.debug(logging_text + step)

                desc = await RO.create("ns", name=db_nsr["name"], datacenter=RO_vim_id,
                                       scenario=nsr_lcm["RO"]["nsd_id"])
                RO_nsr_id = nsr_lcm["RO"]["nsr_id"] = desc["uuid"]
                db_nsr["_admin"]["nsState"] = "INSTANTIATED"
                nsr_lcm["RO"]["nsr_status"] = "BUILD"
            self.update_db("nsrs", nsr_id, db_nsr)

            # wait until NS is ready
            step = ns_status_detailed = "Waiting ns ready at RO"
            db_nsr["detailed-status"] = ns_status_detailed
            self.logger.debug(logging_text + step + " RO_ns_id={}".format(RO_nsr_id))
            deloyment_timeout = 600
            while deloyment_timeout > 0:
                desc = await RO.show("ns", RO_nsr_id)
                ns_status, ns_status_info = RO.check_ns_status(desc)
                nsr_lcm["RO"]["nsr_status"] = ns_status
                if ns_status == "ERROR":
                    raise ROclient.ROClientException(ns_status_info)
                elif ns_status == "BUILD":
                    db_nsr["detailed-status"] = ns_status_detailed + "; {}".format(ns_status_info)
                    self.update_db("nsrs", nsr_id, db_nsr)
                elif ns_status == "ACTIVE":
                    nsr_lcm["nsr_ip"] = RO.get_ns_vnf_ip(desc)
                    break
                else:
                    assert False, "ROclient.check_ns_status returns unknown {}".format(ns_status)

                await asyncio.sleep(5, loop=self.loop)
                deloyment_timeout -= 5
            if deloyment_timeout <= 0:
                raise ROclient.ROClientException("Timeout waiting ns to be ready")
            db_nsr["detailed-status"] = "Configuring vnfr"
            self.update_db("nsrs", nsr_id, db_nsr)

            # The parameters we'll need to deploy a charm
            number_to_configure = 0

            def deploy():
                """An inner function to deploy the charm from either vnf or vdu
                """

                # Login to the VCA.
                # if number_to_configure == 0:
                #     self.logger.debug("Logging into N2VC...")
                #     task = asyncio.ensure_future(self.n2vc.login())
                #     yield from asyncio.wait_for(task, 30.0)
                #     self.logger.debug("Logged into N2VC!")

                ## await self.n2vc.login()

                # Note: The charm needs to exist on disk at the location
                # specified by charm_path.
                base_folder = vnfd["_admin"]["storage"]
                storage_params = self.fs.get_params()
                charm_path = "{}{}/{}/charms/{}".format(
                    storage_params["path"],
                    base_folder["folder"],
                    base_folder["pkg-dir"],
                    proxy_charm
                )

                # Setup the runtime parameters for this VNF
                params['rw_mgmt_ip'] = nsr_lcm['nsr_ip']["vnf"][vnf_index]

                # ns_name will be ignored in the current version of N2VC
                # but will be implemented for the next point release.
                model_name = 'default'
                application_name = self.n2vc.FormatApplicationName(
                    nsr_name,
                    vnf_index,
                    vnfd['name'],
                )

                nsr_lcm["VCA"][vnf_index] = {
                    "model": model_name,
                    "application": application_name,
                    "operational-status": "init",
                    "detailed-status": "",
                    "vnfd_id": vnfd_id,
                }

                self.logger.debug("Task create_ns={} Passing artifacts path '{}' for {}".format(nsr_id, charm_path, proxy_charm))
                task = asyncio.ensure_future(
                    self.n2vc.DeployCharms(
                        model_name,          # The network service name
                        application_name,    # The application name
                        vnfd,                # The vnf descriptor
                        charm_path,          # Path to charm
                        params,              # Runtime params, like mgmt ip
                        {},                  # for native charms only
                        self.n2vc_callback,  # Callback for status changes
                        db_nsr,              # Callback parameter
                        db_nslcmop,
                        vnf_index,           # Callback parameter
                        None,                # Callback parameter (task)
                    )
                )
                task.add_done_callback(functools.partial(self.n2vc_callback, model_name, application_name, None,
                                                         db_nsr, db_nslcmop, vnf_index))
                self.lcm_ns_tasks[nsr_id][nslcmop_id]["create_charm:" + vnf_index] = task

            # TODO: Make this call inside deploy()
            # Login to the VCA. If there are multiple calls to login(),
            # subsequent calls will be a nop and return immediately.
            await self.n2vc.login()

            step = "Looking for needed vnfd to configure"
            self.logger.debug(logging_text + step)
            for c_vnf in nsd["constituent-vnfd"]:
                vnfd_id = c_vnf["vnfd-id-ref"]
                vnf_index = str(c_vnf["member-vnf-index"])
                vnfd = needed_vnfd[vnfd_id]

                # Check if this VNF has a charm configuration
                vnf_config = vnfd.get("vnf-configuration")

                if vnf_config and vnf_config.get("juju"):
                    proxy_charm = vnf_config["juju"]["charm"]
                    params = {}

                    if proxy_charm:
                        if 'initial-config-primitive' in vnf_config:
                            params['initial-config-primitive'] = vnf_config['initial-config-primitive']

                        deploy()
                        number_to_configure += 1

                # Deploy charms for each VDU that supports one.
                for vdu in vnfd['vdu']:
                    vdu_config = vdu.get('vdu-configuration')
                    proxy_charm = None
                    params = {}

                    if vdu_config and vdu_config.get("juju"):
                        proxy_charm = vdu_config["juju"]["charm"]

                        if 'initial-config-primitive' in vdu_config:
                            params['initial-config-primitive'] = vdu_config['initial-config-primitive']

                        if proxy_charm:
                            deploy()
                            number_to_configure += 1

            if number_to_configure:
                db_nsr["config-status"] = "configuring"
                db_nsr["detailed-status"] = "configuring: init: {}".format(number_to_configure)
                db_nslcmop["detailed-status"] = "configuring: init: {}".format(number_to_configure)
            else:
                db_nslcmop["operationState"] = "COMPLETED"
                db_nslcmop["detailed-status"] = "done"
                db_nsr["config-status"] = "configured"
                db_nsr["detailed-status"] = "done"
            db_nsr["operational-status"] = "running"
            self.update_db("nsrs", nsr_id, db_nsr)
            self.update_db("nslcmops", nslcmop_id, db_nslcmop)
            self.logger.debug("Task ns_instantiate={} Exit Ok".format(nsr_id))
            return nsr_lcm

        except (ROclient.ROClientException, DbException, LcmException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {} {}".format(type(e).__name__, e), exc_info=True)
            exc = e
        finally:
            if exc:
                if db_nsr:
                    db_nsr["detailed-status"] = "ERROR {}: {}".format(step, exc)
                    db_nsr["operational-status"] = "failed"
                    self.update_db("nsrs", nsr_id, db_nsr)
                if db_nslcmop:
                    db_nslcmop["detailed-status"] = "FAILED {}: {}".format(step, exc)
                    db_nslcmop["operationState"] = "FAILED"
                    db_nslcmop["statusEnteredTime"] = time()
                    self.update_db("nslcmops", nslcmop_id, db_nslcmop)

    async def ns_terminate(self, nsr_id, nslcmop_id):
        logging_text = "Task ns={} terminate={} ".format(nsr_id, nslcmop_id)
        self.logger.debug(logging_text + "Enter")
        db_nsr = None
        db_nslcmop = None
        exc = None
        step = "Getting nsr, nslcmop from db"
        failed_detail = []   # annotates all failed error messages
        vca_task_list = []
        vca_task_dict = {}
        try:
            db_nslcmop = self.db.get_one("nslcmops", {"_id": nslcmop_id})
            db_nsr = self.db.get_one("nsrs", {"_id": nsr_id})
            # nsd = db_nsr["nsd"]
            nsr_lcm = deepcopy(db_nsr["_admin"]["deployed"])
            if db_nsr["_admin"]["nsState"] == "NOT_INSTANTIATED":
                return
            # TODO ALF remove
            # db_vim = self.db.get_one("vims", {"_id":  db_nsr["datacenter"]})
            # #TODO check if VIM is creating and wait
            # RO_vim_id = db_vim["_admin"]["deployed"]["RO"]

            db_nsr_update = {
                "operational-status": "terminating",
                "config-status": "terminating",
                "detailed-status": "Deleting charms",
            }
            self.update_db_2("nsrs", nsr_id, db_nsr_update)

            try:
                self.logger.debug(logging_text + step)
                for vnf_index, deploy_info in nsr_lcm["VCA"].items():
                    if deploy_info and deploy_info.get("application"):
                        task = asyncio.ensure_future(
                            self.n2vc.RemoveCharms(
                                deploy_info['model'],
                                deploy_info['application'],
                                # self.n2vc_callback,
                                # db_nsr,
                                # db_nslcmop,
                                # vnf_index,
                            )
                        )
                        vca_task_list.append(task)
                        vca_task_dict[vnf_index] = task
                        # task.add_done_callback(functools.partial(self.n2vc_callback, deploy_info['model'],
                        #                                          deploy_info['application'], None, db_nsr,
                        #                                          db_nslcmop, vnf_index))
                        self.lcm_ns_tasks[nsr_id][nslcmop_id]["delete_charm:" + vnf_index] = task
            except Exception as e:
                self.logger.debug(logging_text + "Failed while deleting charms: {}".format(e))
            # remove from RO

            RO = ROclient.ROClient(self.loop, **self.ro_config)
            # Delete ns
            RO_nsr_id = nsr_lcm["RO"].get("nsr_id")
            if RO_nsr_id:
                try:
                    step = db_nsr["detailed-status"] = "Deleting ns at RO"
                    self.logger.debug(logging_text + step)
                    desc = await RO.delete("ns", RO_nsr_id)
                    nsr_lcm["RO"]["nsr_id"] = None
                    nsr_lcm["RO"]["nsr_status"] = "DELETED"
                except ROclient.ROClientException as e:
                    if e.http_code == 404:  # not found
                        nsr_lcm["RO"]["nsr_id"] = None
                        nsr_lcm["RO"]["nsr_status"] = "DELETED"
                        self.logger.debug(logging_text + "RO_ns_id={} already deleted".format(RO_nsr_id))
                    elif e.http_code == 409:   #conflict
                        failed_detail.append("RO_ns_id={} delete conflict: {}".format(RO_nsr_id, e))
                        self.logger.debug(logging_text + failed_detail[-1])
                    else:
                        failed_detail.append("RO_ns_id={} delete error: {}".format(RO_nsr_id, e))
                        self.logger.error(logging_text + failed_detail[-1])

            # Delete nsd
            RO_nsd_id = nsr_lcm["RO"]["nsd_id"]
            if RO_nsd_id:
                try:
                    step = db_nsr["detailed-status"] = "Deleting nsd at RO"
                    desc = await RO.delete("nsd", RO_nsd_id)
                    self.logger.debug(logging_text + "RO_nsd_id={} deleted".format(RO_nsd_id))
                    nsr_lcm["RO"]["nsd_id"] = None
                except ROclient.ROClientException as e:
                    if e.http_code == 404:  # not found
                        nsr_lcm["RO"]["nsd_id"] = None
                        self.logger.debug(logging_text + "RO_nsd_id={} already deleted".format(RO_nsd_id))
                    elif e.http_code == 409:   #conflict
                        failed_detail.append("RO_nsd_id={} delete conflict: {}".format(RO_nsd_id, e))
                        self.logger.debug(logging_text + failed_detail[-1])
                    else:
                        failed_detail.append("RO_nsd_id={} delete error: {}".format(RO_nsd_id, e))
                        self.logger.error(logging_text + failed_detail[-1])

            for vnf_id, RO_vnfd_id in nsr_lcm["RO"]["vnfd_id"].items():
                if not RO_vnfd_id:
                    continue
                try:
                    step = db_nsr["detailed-status"] = "Deleting vnfd={} at RO".format(vnf_id)
                    desc = await RO.delete("vnfd", RO_vnfd_id)
                    self.logger.debug(logging_text + "RO_vnfd_id={} deleted".format(RO_vnfd_id))
                    nsr_lcm["RO"]["vnfd_id"][vnf_id] = None
                except ROclient.ROClientException as e:
                    if e.http_code == 404:  # not found
                        nsr_lcm["RO"]["vnfd_id"][vnf_id] = None
                        self.logger.debug(logging_text + "RO_vnfd_id={} already deleted ".format(RO_vnfd_id))
                    elif e.http_code == 409:   #conflict
                        failed_detail.append("RO_vnfd_id={} delete conflict: {}".format(RO_vnfd_id, e))
                        self.logger.debug(logging_text + failed_detail[-1])
                    else:
                        failed_detail.append("RO_vnfd_id={} delete error: {}".format(RO_vnfd_id, e))
                        self.logger.error(logging_text + failed_detail[-1])

            if vca_task_list:
                await asyncio.wait(vca_task_list, timeout=300)
            for vnf_index, task in vca_task_dict.items():
                if task.cancelled():
                    failed_detail.append("VCA[{}] Deletion has been cancelled".format(vnf_index))
                elif task.done():
                    exc = task.exception()
                    if exc:
                        failed_detail.append("VCA[{}] Deletion exception: {}".format(vnf_index, exc))
                    else:
                        nsr_lcm["VCA"][vnf_index] = None
                else:  # timeout
                    # TODO Should it be cancelled?!!
                    task.cancel()
                    failed_detail.append("VCA[{}] Deletion timeout".format(vnf_index))

            if failed_detail:
                self.logger.error(logging_text + " ;".join(failed_detail))
                db_nsr_update = {
                    "operational-status": "failed",
                    "detailed-status": "Deletion errors " + "; ".join(failed_detail),
                    "_admin": {"deployed": nsr_lcm, }
                }
                db_nslcmop_update = {
                    "detailedStatus": "; ".join(failed_detail),
                    "operationState": "FAILED",
                    "statusEnteredTime": time()
                }
            elif db_nslcmop["operationParams"].get("autoremove"):
                self.db.del_one("nsrs", {"_id": nsr_id})
                self.db.del_list("nslcmops", {"nsInstanceId": nsr_id})
            else:
                db_nsr_update = {
                    "operational-status": "terminated",
                    "detailed-status": "Done",
                    "_admin": {"deployed": nsr_lcm, "nsState": "NOT_INSTANTIATED"}
                }
                db_nslcmop_update = {
                    "detailedStatus": "Done",
                    "operationState": "COMPLETED",
                    "statusEnteredTime": time()
                }
            self.logger.debug(logging_text + "Exit")

        except (ROclient.ROClientException, DbException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {}".format(e), exc_info=True)
            exc = e
        finally:
            if exc and db_nslcmop:
                db_nslcmop_update = {
                    "detailed-status": "FAILED {}: {}".format(step, exc),
                    "operationState": "FAILED",
                    "statusEnteredTime": time(),
                }
            if db_nslcmop_update:
                self.update_db_2("nslcmops", nslcmop_id, db_nslcmop_update)
            if db_nsr_update:
                self.update_db_2("nsrs", nsr_id, db_nsr_update)

    async def ns_action(self, nsr_id, nslcmop_id):
        logging_text = "Task ns={} action={} ".format(nsr_id, nslcmop_id)
        self.logger.debug(logging_text + "Enter")
        # get all needed from database
        db_nsr = None
        db_nslcmop = None
        db_nslcmop_update = None
        exc = None
        step = "Getting nsr, nslcmop"
        try:
            db_nslcmop = self.db.get_one("nslcmops", {"_id": nslcmop_id})
            db_nsr = self.db.get_one("nsrs", {"_id": nsr_id})
            nsr_lcm = db_nsr["_admin"].get("deployed")
            vnf_index = db_nslcmop["operationParams"]["vnf_member_index"]

            #TODO check if ns is in a proper status
            vca_deployed = nsr_lcm["VCA"].get(vnf_index)
            if not vca_deployed:
                raise LcmException("charm for vnf_member_index={} is not deployed".format(vnf_index))
            model_name = vca_deployed.get("model")
            application_name = vca_deployed.get("application")
            if not model_name or not application_name:
                raise LcmException("charm for vnf_member_index={} is not properly deployed".format(vnf_index))
            if vca_deployed["operational-status"] != "active":
                raise LcmException("charm for vnf_member_index={} operational_status={} not 'active'".format(
                    vnf_index, vca_deployed["operational-status"]))
            primitive = db_nslcmop["operationParams"]["primitive"]
            primitive_params = db_nslcmop["operationParams"]["primitive_params"]
            callback = None     # self.n2vc_callback
            callback_args = ()  # [db_nsr, db_nslcmop, vnf_index, None]
            await self.n2vc.login()
            task = asyncio.ensure_future(
                self.n2vc.ExecutePrimitive(
                    model_name,
                    application_name,
                    primitive, callback,
                    *callback_args,
                    **primitive_params
                )
            )
            # task.add_done_callback(functools.partial(self.n2vc_callback, model_name, application_name, None,
            #                                          db_nsr, db_nslcmop, vnf_index))
            # self.lcm_ns_tasks[nsr_id][nslcmop_id]["action: " + primitive] = task
            # wait until completed with timeout
            await asyncio.wait((task,), timeout=300)

            result = "FAILED"  # by default
            result_detail = ""
            if task.cancelled():
                db_nslcmop["detailedStatus"] = "Task has been cancelled"
            elif task.done():
                exc = task.exception()
                if exc:
                    result_detail = str(exc)
                else:
                    self.logger.debug(logging_text + " task Done")
                    # TODO revise with Adam if action is finished and ok when task is done or callback is needed
                    result = "COMPLETED"
                    result_detail = "Done"
            else:   # timeout
                # TODO Should it be cancelled?!!
                task.cancel()
                result_detail = "timeout"

            db_nslcmop_update = {
                "detailedStatus": result_detail,
                "operationState": result,
                "statusEnteredTime": time()
            }
            self.logger.debug(logging_text + " task Done with result {} {}".format(result, result_detail))
            return  # database update is called inside finally

        except (DbException, LcmException) as e:
            self.logger.error(logging_text + "Exit Exception {}".format(e))
            exc = e
        except Exception as e:
            self.logger.critical(logging_text + "Exit Exception {} {}".format(type(e).__name__, e), exc_info=True)
            exc = e
        finally:
            if exc and db_nslcmop:
                db_nslcmop_update = {
                    "detailed-status": "FAILED {}: {}".format(step, exc),
                    "operationState": "FAILED",
                    "statusEnteredTime": time(),
                }
            if db_nslcmop_update:
                self.update_db_2("nslcmops", nslcmop_id, db_nslcmop_update)

    async def test(self, param=None):
        self.logger.debug("Starting/Ending test task: {}".format(param))

    def cancel_tasks(self, topic, _id):
        """
        Cancel all active tasks of a concrete nsr or vim identified for _id
        :param topic: can be ns or vim_account
        :param _id:  nsr or vim identity
        :return: None, or raises an exception if not possible
        """
        if topic == "ns":
            lcm_tasks = self.lcm_ns_tasks
        elif topic== "vim_account":
            lcm_tasks = self.lcm_vim_tasks
        elif topic== "sdn":
            lcm_tasks = self.lcm_sdn_tasks

        if not lcm_tasks.get(_id):
            return
        for order_id, tasks_set in lcm_tasks[_id].items():
            for task_name, task in tasks_set.items():
                result = task.cancel()
                if result:
                    self.logger.debug("{} _id={} order_id={} task={} cancelled".format(topic, _id, order_id, task_name))
        lcm_tasks[_id] = {}

    async def kafka_ping(self):
        self.logger.debug("Task kafka_ping Enter")
        consecutive_errors = 0
        first_start = True
        kafka_has_received = False
        self.pings_not_received = 1
        while True:
            try:
                await self.msg.aiowrite("admin", "ping", {"from": "lcm", "to": "lcm"},  self.loop)
                # time between pings are low when it is not received and at starting
                wait_time = 5 if not kafka_has_received else 120
                if not self.pings_not_received:
                    kafka_has_received = True
                self.pings_not_received += 1
                await asyncio.sleep(wait_time, loop=self.loop)
                if self.pings_not_received > 10:
                    raise LcmException("It is not receiving pings from Kafka bus")
                consecutive_errors = 0
                first_start = False
            except LcmException:
                raise
            except Exception as e:
                # if not first_start is the first time after starting. So leave more time and wait
                # to allow kafka starts
                if consecutive_errors == 8 if not first_start else 30:
                    self.logger.error("Task kafka_read task exit error too many errors. Exception: {}".format(e))
                    raise
                consecutive_errors += 1
                self.logger.error("Task kafka_read retrying after Exception {}".format(e))
                wait_time = 1 if not first_start else 5
                await asyncio.sleep(wait_time, loop=self.loop)

    async def kafka_read(self):
        self.logger.debug("Task kafka_read Enter")
        order_id = 1
        # future = asyncio.Future()
        consecutive_errors = 0
        first_start = True
        while consecutive_errors < 10:
            try:
                topics = ("admin", "ns", "vim_account", "sdn")
                topic, command, params = await self.msg.aioread(topics, self.loop)
                self.logger.debug("Task kafka_read receives {} {}: {}".format(topic, command, params))
                consecutive_errors = 0
                first_start = False
                order_id += 1
                if command == "exit":
                    print("Bye!")
                    break
                elif command.startswith("#"):
                    continue
                elif command == "echo":
                    # just for test
                    print(params)
                    sys.stdout.flush()
                    continue
                elif command == "test":
                    asyncio.Task(self.test(params), loop=self.loop)
                    continue

                if topic == "admin":
                    if command == "ping" and params["to"] == "lcm" and params["from"] == "lcm":
                        self.pings_not_received = 0
                    continue
                elif topic == "ns":
                    if command == "instantiate":
                        # self.logger.debug("Deploying NS {}".format(nsr_id))
                        nslcmop = params
                        nslcmop_id = nslcmop["_id"]
                        nsr_id = nslcmop["nsInstanceId"]
                        task = asyncio.ensure_future(self.ns_instantiate(nsr_id, nslcmop_id))
                        if nsr_id not in self.lcm_ns_tasks:
                            self.lcm_ns_tasks[nsr_id] = {}
                        self.lcm_ns_tasks[nsr_id][nslcmop_id] = {"ns_instantiate": task}
                        continue
                    elif command == "terminate":
                        # self.logger.debug("Deleting NS {}".format(nsr_id))
                        nslcmop = params
                        nslcmop_id = nslcmop["_id"]
                        nsr_id = nslcmop["nsInstanceId"]
                        self.cancel_tasks(topic, nsr_id)
                        task = asyncio.ensure_future(self.ns_terminate(nsr_id, nslcmop_id))
                        if nsr_id not in self.lcm_ns_tasks:
                            self.lcm_ns_tasks[nsr_id] = {}
                        self.lcm_ns_tasks[nsr_id][nslcmop_id] = {"ns_terminate": task}
                        continue
                    elif command == "action":
                        # self.logger.debug("Update NS {}".format(nsr_id))
                        nslcmop = params
                        nslcmop_id = nslcmop["_id"]
                        nsr_id = nslcmop["nsInstanceId"]
                        task = asyncio.ensure_future(self.ns_action(nsr_id, nslcmop_id))
                        if nsr_id not in self.lcm_ns_tasks:
                            self.lcm_ns_tasks[nsr_id] = {}
                        self.lcm_ns_tasks[nsr_id][nslcmop_id] = {"ns_action": task}
                        continue
                    elif command == "show":
                        try:
                            db_nsr = self.db.get_one("nsrs", {"_id": nsr_id})
                            print(
                            "nsr:\n    _id={}\n    operational-status: {}\n    config-status: {}\n    detailed-status: "
                            "{}\n    deploy: {}\n    tasks: {}".format(
                                nsr_id, db_nsr["operational-status"],
                                db_nsr["config-status"], db_nsr["detailed-status"],
                                db_nsr["_admin"]["deployed"], self.lcm_ns_tasks.get(nsr_id)))
                        except Exception as e:
                            print("nsr {} not found: {}".format(nsr_id, e))
                        sys.stdout.flush()
                        continue
                    elif command == "deleted":
                        continue  # TODO cleaning of task just in case should be done
                elif topic == "vim_account":
                    vim_id = params["_id"]
                    if command == "create":
                        task = asyncio.ensure_future(self.vim_create(params, order_id))
                        if vim_id not in self.lcm_vim_tasks:
                            self.lcm_vim_tasks[vim_id] = {}
                        self.lcm_vim_tasks[vim_id][order_id] = {"vim_create": task}
                        continue
                    elif command == "delete":
                        self.cancel_tasks(topic, vim_id)
                        task = asyncio.ensure_future(self.vim_delete(vim_id, order_id))
                        if vim_id not in self.lcm_vim_tasks:
                            self.lcm_vim_tasks[vim_id] = {}
                        self.lcm_vim_tasks[vim_id][order_id] = {"vim_delete": task}
                        continue
                    elif command == "show":
                        print("not implemented show with vim_account")
                        sys.stdout.flush()
                        continue
                    elif command == "edit":
                        task = asyncio.ensure_future(self.vim_edit(vim_id, order_id))
                        if vim_id not in self.lcm_vim_tasks:
                            self.lcm_vim_tasks[vim_id] = {}
                        self.lcm_vim_tasks[vim_id][order_id] = {"vim_edit": task}
                        continue
                elif topic == "sdn":
                    _sdn_id = params["_id"]
                    if command == "create":
                        task = asyncio.ensure_future(self.sdn_create(params, order_id))
                        if _sdn_id not in self.lcm_sdn_tasks:
                            self.lcm_sdn_tasks[_sdn_id] = {}
                        self.lcm_sdn_tasks[_sdn_id][order_id] = {"sdn_create": task}
                        continue
                    elif command == "delete":
                        self.cancel_tasks(topic, _sdn_id)
                        task = asyncio.ensure_future(self.sdn_delete(_sdn_id, order_id))
                        if _sdn_id not in self.lcm_sdn_tasks:
                            self.lcm_sdn_tasks[_sdn_id] = {}
                        self.lcm_sdn_tasks[_sdn_id][order_id] = {"sdn_delete": task}
                        continue
                    elif command == "edit":
                        task = asyncio.ensure_future(self.sdn_edit(_sdn_id, order_id))
                        if _sdn_id not in self.lcm_sdn_tasks:
                            self.lcm_sdn_tasks[_sdn_id] = {}
                        self.lcm_sdn_tasks[_sdn_id][order_id] = {"sdn_edit": task}
                        continue
                self.logger.critical("unknown topic {} and command '{}'".format(topic, command))
            except Exception as e:
                # if not first_start is the first time after starting. So leave more time and wait
                # to allow kafka starts
                if consecutive_errors == 8 if not first_start else 30:
                    self.logger.error("Task kafka_read task exit error too many errors. Exception: {}".format(e))
                    raise
                consecutive_errors += 1
                self.logger.error("Task kafka_read retrying after Exception {}".format(e))
                wait_time = 2 if not first_start else 5
                await asyncio.sleep(wait_time, loop=self.loop)

        # self.logger.debug("Task kafka_read terminating")
        self.logger.debug("Task kafka_read exit")

    def start(self):
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(asyncio.gather(
            self.kafka_read(),
            self.kafka_ping()
        ))
        # TODO
        # self.logger.debug("Terminating cancelling creation tasks")
        # self.cancel_tasks("ALL", "create")
        # timeout = 200
        # while self.is_pending_tasks():
        #     self.logger.debug("Task kafka_read terminating. Waiting for tasks termination")
        #     await asyncio.sleep(2, loop=self.loop)
        #     timeout -= 2
        #     if not timeout:
        #         self.cancel_tasks("ALL", "ALL")
        self.loop.close()
        self.loop = None
        if self.db:
            self.db.db_disconnect()
        if self.msg:
            self.msg.disconnect()
        if self.fs:
            self.fs.fs_disconnect()


    def read_config_file(self, config_file):
        # TODO make a [ini] + yaml inside parser
        # the configparser library is not suitable, because it does not admit comments at the end of line,
        # and not parse integer or boolean
        try:
            with open(config_file) as f:
                conf = yaml.load(f)
            for k, v in environ.items():
                if not k.startswith("OSMLCM_"):
                    continue
                k_items = k.lower().split("_")
                c = conf
                try:
                    for k_item in k_items[1:-1]:
                        if k_item in ("ro", "vca"):
                            # put in capital letter
                            k_item = k_item.upper()
                        c = c[k_item]
                    if k_items[-1] == "port":
                        c[k_items[-1]] = int(v)
                    else:
                        c[k_items[-1]] = v
                except Exception as e:
                    self.logger.warn("skipping environ '{}' on exception '{}'".format(k, e))

            return conf
        except Exception as e:
            self.logger.critical("At config file '{}': {}".format(config_file, e))
            exit(1)


if __name__ == '__main__':

    config_file = "lcm.cfg"
    lcm = Lcm(config_file)

    lcm.start()
