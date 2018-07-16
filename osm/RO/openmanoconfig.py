#!/usr/bin/env python
# -*- coding: utf-8 -*-

##
# Copyright 2015 Telefónica Investigación y Desarrollo, S.A.U.
# This file is part of openmano
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
# contact with: nfvlabs@tid.es
##


"""
Read openmanod.cfg file and creates envioronment variables for openmano client
Call it wusing execution quotes, or copy paste the output to set your shell envioronment
It read database to look for a ninc tenant / datacenter
"""

from __future__ import print_function
from  os import environ
from openmanod import load_configuration
#from socket import gethostname
from db_base import db_base_Exception
import nfvo_db
import getopt
import sys


__author__="Alfonso Tierno, Gerardo Garcia, Pablo Montes"
__date__ ="$26-aug-2014 11:09:29$"
__version__="0.0.1-r509"
version_date="Oct 2016"
database_version="0.16"      #expected database schema version


def usage():
    print("Usage: ", sys.argv[0], "[options]")
    print("      -v|--version: prints current version")
    print("      -c|--config [configuration_file]: loads the configuration file (default: openmanod.cfg)")
    print("      -h|--help: shows this help")
    return


if __name__ == "__main__":
    # Read parameters and configuration file
    try:
        # load parameters and configuration
        opts, args = getopt.getopt(sys.argv[1:], "vhc:",
                                   ["config=", "help", "version"])
        config_file = 'openmanod.cfg'

        for o, a in opts:
            if o in ("-v", "--version"):
                print("openmanoconfig.py version " + __version__ + ' ' + version_date)
                print("(c) Copyright Telefonica")
                exit()
            elif o in ("-h", "--help"):
                usage()
                exit()
            elif o in ("-c", "--config"):
                config_file = a
            else:
                assert False, "Unhandled option"
        global_config = load_configuration(config_file)
        if global_config["http_host"] == "0.0.0.0":
            global_config["http_host"] = "localhost" #gethostname()
        environ["OPENMANO_HOST"]=global_config["http_host"]
        print("export OPENMANO_HOST='{}'".format(global_config["http_host"]))
        environ["OPENMANO_PORT"] = str(global_config["http_port"])
        print("export OPENMANO_PORT={}".format(global_config["http_port"]))

        mydb = nfvo_db.nfvo_db();
        mydb.connect(global_config['db_host'], global_config['db_user'], global_config['db_passwd'], global_config['db_name'])
        try:
            tenants = mydb.get_rows(FROM="nfvo_tenants")
            if not tenants:
                print("#No tenant found", file=sys.stderr)
            elif len(tenants) > 1:
                print("#Found several tenants export OPENMANO_TENANT=", file=sys.stderr, end="")
                for tenant in tenants:
                    print(" '{}'".format(tenant["name"]), file=sys.stderr, end="")
                print("")
            else:
                environ["OPENMANO_TENANT"] = tenants[0]["name"]
                print("export OPENMANO_TENANT='{}'".format(tenants[0]["name"]))

            dcs = mydb.get_rows(FROM="datacenters")
            if not dcs:
                print("#No datacenter found", file=sys.stderr)
            elif len(dcs) > 1:
                print("#Found several datacenters export OPENMANO_DATACENTER=", file=sys.stderr, end="")
                for dc in dcs:
                    print(" '{}'".format(dc["name"]), file=sys.stderr, end="")
                print("")
            else:
                environ["OPENMANO_DATACENTER"] = dcs[0]["name"]
                print("export OPENMANO_DATACENTER='{}'".format(dcs[0]["name"]))

        except db_base_Exception as e:
            print("#DATABASE is not a MANO one or it is a '0.0' version. Try to upgrade to version '{}' with \
                            './database_utils/migrate_mano_db.sh'".format(database_version), file=sys.stderr)
            exit(-1)



    except db_base_Exception as e:
        print("#"+str(e), file=sys.stderr)
        exit(-1)

    except SystemExit:
        pass
