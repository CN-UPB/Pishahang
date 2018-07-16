#!/usr/bin/python3

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

import argparse
import logging
import os
import re
import subprocess
import sys
import tempfile
import requests
import json


class OpenmanoCommandFailed(Exception):
    pass


class OpenmanoUnexpectedOutput(Exception):
    pass


class VNFExistsError(Exception):
    pass


class InstanceStatusError(Exception):
    pass


class OpenmanoHttpAPI(object):
    def __init__(self, log, host, port, tenant):
        self._log = log
        self._host = host
        self._port = port
        self._tenant = tenant

        self._session = requests.Session()

    def instances(self):
        url = "http://{host}:{port}/openmano/{tenant}/instances".format(
                host=self._host,
                port=self._port,
                tenant=self._tenant,
                )

        resp = self._session.get(url)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise InstanceStatusError(e)

        return resp.json()["instances"]

    def get_instance(self, instance_uuid):
        url = "http://{host}:{port}/openmano/{tenant}/instances/{instance}".format(
                host=self._host,
                port=self._port,
                tenant=self._tenant,
                instance=instance_uuid,
                )

        resp = self._session.get(url)
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise InstanceStatusError(e)

        return resp.json()

    def get_instance_vm_console_url(self, instance_uuid, vim_uuid):
        url = "http://{host}:{port}/openmano/{tenant}/instances/{instance}/action".format(
            host=self._host,
            port=self._port,
            tenant=self._tenant,
            instance=instance_uuid,
            )

        console_types = ("novnc", "spice-html5", "xvpnvc", "rdp-html5")
        for console_type in console_types:
            payload_input = {"console":console_type, "vms":[vim_uuid]}
            payload_data = json.dumps(payload_input)
            resp = self._session.post(url, headers={'content-type': 'application/json'},
                                      data=payload_data)
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise InstanceStatusError(e)
            result = resp.json()
            if vim_uuid in result and (result[vim_uuid]["vim_result"] == 1 or result[vim_uuid]["vim_result"] == 200):
                return result[vim_uuid]["description"]

        return None

    def vnfs(self):
        url = "http://{host}:{port}/openmano/{tenant}/vnfs".format(
            host=self._host,
            port=self._port,
            tenant=self._tenant
            )
        resp = self._session.get(url, headers={'content-type': 'application/json'})
        
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise InstanceStatusError(e)

        return resp.json()

    def vnf(self, vnf_id):
        vnf_uuid = None
        try:
            vnfs = self.vnfs()
            for vnf in vnfs["vnfs"]:
                # Rift vnf ID gets mapped to osm_id in OpenMano
                if vnf_id == vnf["osm_id"]:
                    vnf_uuid = vnf["uuid"]
                    break
        except Exception as e:
            raise e    

        if not vnf_uuid:
            return None
        else:
            url = "http://{host}:{port}/openmano/{tenant}/vnfs/{uuid}".format(
                host=self._host,
                port=self._port,
                tenant=self._tenant,
                uuid=vnf_uuid
                )
            resp = self._session.get(url, headers={'content-type': 'application/json'})
        
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise InstanceStatusError(e)

            return resp.json()['vnf']

    def scenarios(self):
        url = "http://{host}:{port}/openmano/{tenant}/scenarios".format(
            host=self._host,
            port=self._port,
            tenant=self._tenant
            )
        resp = self._session.get(url, headers={'content-type': 'application/json'})
        
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise InstanceStatusError(e)

        return resp.json()

    def scenario(self, scenario_id):
        scenario_uuid = None
        try:
            scenarios = self.scenarios()
            for scenario in scenarios["scenarios"]:
                # Rift NS ID gets mapped to osm_id in OpenMano
                if scenario_id == scenario["osm_id"]:
                    scenario_uuid = scenario["uuid"]
                    break
        except Exception as e:
            raise e    

        if not scenario_uuid:
            return None
        else:
            url = "http://{host}:{port}/openmano/{tenant}/scenarios/{uuid}".format(
                host=self._host,
                port=self._port,
                tenant=self._tenant,
                uuid=scenario_uuid
                )
            resp = self._session.get(url, headers={'content-type': 'application/json'})
        
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise InstanceStatusError(e)

            return resp.json()['scenario']

    def post_vnfd_v3(self, vnfd_body):
        # Check if the VNF is present at the RO
        vnf_rift_id = vnfd_body["vnfd:vnfd-catalog"]["vnfd"][0]["id"]
        vnf_check = self.vnf(vnf_rift_id)
        
        if not vnf_check:  
            url = "http://{host}:{port}/openmano/v3/{tenant}/vnfd".format(
                host=self._host,
                port=self._port,
                tenant=self._tenant
                )
            payload_data = json.dumps(vnfd_body)
            resp = self._session.post(url, headers={'content-type': 'application/json'},
                                        data=payload_data)
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise InstanceStatusError(e)

            return resp.json()['vnfd'][0]

        else:
            return vnf_check

    def post_nsd_v3(self, nsd_body):
        # Check if the NS (Scenario) is present at the RO
        scenario_rift_id = nsd_body["nsd:nsd-catalog"]["nsd"][0]["id"]
        scenario_check = self.scenario(scenario_rift_id)

        if not scenario_check:   
            url = "http://{host}:{port}/openmano/v3/{tenant}/nsd".format(
                host=self._host,
                port=self._port,
                tenant=self._tenant
                )
            payload_data = json.dumps(nsd_body)
            resp = self._session.post(url, headers={'content-type': 'application/json'},
                                        data=payload_data)
            try:
                resp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                raise InstanceStatusError(e)

            return resp.json()['nsd'][0]
        else:
            return scenario_check        


class OpenmanoCliAPI(object):
    """ This class implements the necessary funtionality to interact with  """

    CMD_TIMEOUT = 120

    def __init__(self, log, host, port, tenant):
        self._log = log
        self._host = host
        self._port = port
        self._tenant = tenant

    @staticmethod
    def openmano_cmd_path():
        return os.path.join(
               os.environ["RIFT_INSTALL"],
               "usr/bin/openmano"
               )

    def _openmano_cmd(self, arg_list, expected_lines=None):
        cmd_args = list(arg_list)
        cmd_args.insert(0, self.openmano_cmd_path())

        env = {
                "OPENMANO_HOST": self._host,
                "OPENMANO_PORT": str(self._port),
                "OPENMANO_TENANT": self._tenant,
                }

        self._log.debug(
                "Running openmano command (%s) using env (%s)",
                subprocess.list2cmdline(cmd_args),
                env,
                )

        proc = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                env=env
                )
        try:
            stdout, stderr = proc.communicate(timeout=self.CMD_TIMEOUT)
        except subprocess.TimeoutExpired:
            self._log.error("Openmano command timed out")
            proc.terminate()
            stdout, stderr = proc.communicate(timeout=self.CMD_TIMEOUT)

        if proc.returncode != 0:
            self._log.error(
                    "Openmano command %s failed (rc=%s) with stdout: %s",
                    cmd_args[1], proc.returncode, stdout
                    )
            raise OpenmanoCommandFailed(stdout)

        self._log.debug("Openmano command completed with stdout: %s", stdout)

        output_lines = stdout.splitlines()
        if expected_lines is not None:
            if len(output_lines) != expected_lines:
                msg = "Expected %s lines from openmano command. Got %s" % (expected_lines, len(output_lines))
                self._log.error(msg)
                raise OpenmanoUnexpectedOutput(msg)

        return output_lines


    def vnf_create(self, vnf_yaml_str):
        """ Create a Openmano VNF from a Openmano VNF YAML string """

        self._log.debug("Creating VNF: %s", vnf_yaml_str)

        with tempfile.NamedTemporaryFile() as vnf_file_hdl:
            vnf_file_hdl.write(vnf_yaml_str.encode())
            vnf_file_hdl.flush()

            try:
                output_lines = self._openmano_cmd(
                        ["vnf-create", vnf_file_hdl.name],
                        expected_lines=1
                        )
            except OpenmanoCommandFailed as e:
                if "already in use" in str(e):
                    raise VNFExistsError("VNF was already added")
                raise

        vnf_info_line = output_lines[0]
        vnf_id, vnf_name = vnf_info_line.split(" ", 1)

        self._log.info("VNF %s Created: %s", vnf_name, vnf_id)

        return vnf_id, vnf_name

    def vnf_delete(self, vnf_uuid):
        self._openmano_cmd(
                ["vnf-delete", vnf_uuid, "-f"],
                )

        self._log.info("VNF Deleted: %s", vnf_uuid)

    def vnf_list(self):
        try:
            output_lines = self._openmano_cmd(
                    ["vnf-list"],
                    )

        except OpenmanoCommandFailed as e:
            self._log.warning("Vnf listing returned an error: %s", str(e))
            return {}

        name_uuid_map = {}
        for line in output_lines:
            line = line.strip()
            uuid, name = line.split(" ", 1)
            name_uuid_map[name.strip()] = uuid.strip()

        self._log.debug("VNF list: {}".format(name_uuid_map))
        return name_uuid_map

    def ns_create(self, ns_yaml_str, name=None):
        self._log.info("Creating NS: %s", ns_yaml_str)

        with tempfile.NamedTemporaryFile() as ns_file_hdl:
            ns_file_hdl.write(ns_yaml_str.encode())
            ns_file_hdl.flush()

            cmd_args = ["scenario-create", ns_file_hdl.name]
            if name is not None:
                cmd_args.extend(["--name", name])

            output_lines = self._openmano_cmd(
                    cmd_args,
                    expected_lines=1
                    )

        ns_info_line = output_lines[0]
        ns_id, ns_name = ns_info_line.split(" ", 1)

        self._log.info("NS %s Created: %s", ns_name, ns_id)

        return ns_id, ns_name

    def ns_list(self):
        self._log.debug("Getting NS list")

        try:
            output_lines = self._openmano_cmd(
                    ["scenario-list"],
                    )

        except OpenmanoCommandFailed as e:
            self._log.warning("NS listing returned an error: %s", str(e))
            return {}

        name_uuid_map = {}
        for line in output_lines:
            line = line.strip()
            uuid, name = line.split(" ", 1)
            name_uuid_map[name.strip()] = uuid.strip()

        self._log.debug("Scenario list: {}".format(name_uuid_map))
        return name_uuid_map

    def ns_delete(self, ns_uuid):
        self._log.info("Deleting NS: %s", ns_uuid)

        self._openmano_cmd(
                ["scenario-delete", ns_uuid, "-f"],
                )

        self._log.info("NS Deleted: %s", ns_uuid)

    def ns_instance_list(self):
        self._log.debug("Getting NS instance list")

        try:
            output_lines = self._openmano_cmd(
                    ["instance-scenario-list"],
                    )

        except OpenmanoCommandFailed as e:
            self._log.warning("Instance scenario listing returned an error: %s", str(e))
            return {}

        if "No scenario instances were found" in output_lines[0]:
            self._log.debug("No openmano instances were found")
            return {}

        name_uuid_map = {}
        for line in output_lines:
            line = line.strip()
            uuid, name = line.split(" ", 1)
            name_uuid_map[name.strip()] = uuid.strip()

        self._log.debug("Instance Scenario list: {}".format(name_uuid_map))
        return name_uuid_map

    def ns_instance_scenario_create(self, instance_yaml_str):
        """ Create a Openmano NS instance from input YAML string """

        self._log.debug("Instantiating instance: %s", instance_yaml_str)

        with tempfile.NamedTemporaryFile() as ns_instance_file_hdl:
            ns_instance_file_hdl.write(instance_yaml_str.encode())
            ns_instance_file_hdl.flush()

            try:
                output_lines = self._openmano_cmd(
                        ["instance-scenario-create", ns_instance_file_hdl.name],
                        expected_lines=1
                        )
            except OpenmanoCommandFailed as e:
                raise

        uuid, _ = output_lines[0].split(" ", 1)

        self._log.info("NS Instance Created: %s", uuid)

        return uuid


    def ns_vim_network_create(self, net_create_yaml_str,datacenter_name):
        """ Create a Openmano VIM network from input YAML string """

        self._log.debug("Creating VIM network instance: %s, DC %s", net_create_yaml_str,datacenter_name)

        with tempfile.NamedTemporaryFile() as net_create_file_hdl:
            net_create_file_hdl.write(net_create_yaml_str.encode())
            net_create_file_hdl.flush()

            try:
                output_lines = self._openmano_cmd(
                        ["vim-net-create","--datacenter", datacenter_name, net_create_file_hdl.name],
                        expected_lines=1
                        )
            except OpenmanoCommandFailed as e:
                raise

        uuid, _ = output_lines[0].split(" ", 1)

        self._log.info("VIM Networks created in DC %s with ID: %s", datacenter_name, uuid)

        return uuid

    def ns_vim_network_delete(self, network_name,datacenter_name):
        """ Delete a Openmano VIM network with given name """

        self._log.debug("Deleting VIM network instance: %s, DC %s", network_name,datacenter_name)
        try:
            output_lines = self._openmano_cmd(
                    ["vim-net-delete","--datacenter", datacenter_name, network_name],
                    expected_lines=1
                    )
        except OpenmanoCommandFailed as e:
            raise
        self._log.info("VIM Network deleted in DC %s with name: %s", datacenter_name, network_name)


    def ns_instantiate(self, scenario_name, instance_name, datacenter_name=None):
        self._log.info(
                "Instantiating NS %s using instance name %s",
                scenario_name,
                instance_name,
                )

        cmd_args = ["scenario-deploy", scenario_name, instance_name]
        if datacenter_name is not None:
            cmd_args.extend(["--datacenter", datacenter_name])

        output_lines = self._openmano_cmd(
                cmd_args,
                expected_lines=4
                )

        uuid, _ = output_lines[0].split(" ", 1)

        self._log.info("NS Instance Created: %s", uuid)

        return uuid

    def ns_terminate(self, ns_instance_name):
        self._log.info("Terminating NS: %s", ns_instance_name)

        self._openmano_cmd(
                ["instance-scenario-delete", ns_instance_name, "-f"],
                )

        self._log.info("NS Instance Deleted: %s", ns_instance_name)

    def datacenter_list(self):
        lines = self._openmano_cmd(["datacenter-list",])

        # The results returned from openmano are formatted with whitespace and
        # datacenter names may contain whitespace as well, so we use a regular
        # expression to parse each line of the results return from openmano to
        # extract the uuid and name of a datacenter.
        hex = '[0-9a-fA-F]'
        uuid_pattern = '(xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)'.replace('x', hex)
        name_pattern = '(.+?)'
        datacenter_regex = re.compile(r'{uuid}\s+\b{name}\s*$'.format(
            uuid=uuid_pattern,
            name=name_pattern,
            ))

        # Parse the results for the datacenter uuids and names
        datacenters = list()
        for line in lines:
            result = datacenter_regex.match(line)
            if result is not None:
                uuid, name = result.groups()
                datacenters.append((uuid, name))

        return datacenters


def valid_uuid(uuid_str):
    uuid_re = re.compile(
            "^xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx$".replace('x', '[0-9a-fA-F]')
            )

    if not uuid_re.match(uuid_str):
        raise argparse.ArgumentTypeError("Got a valid uuid: %s" % uuid_str)

    return uuid_str


def parse_args(argv=sys.argv[1:]):
    """ Parse the command line arguments

    Arguments:
        argv - The list of arguments to parse

    Returns:
        Argparse Namespace instance
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-d', '--host',
        default='localhost',
        help="Openmano host/ip",
        )

    parser.add_argument(
        '-p', '--port',
        default='9090',
        help="Openmano port",
        )

    parser.add_argument(
        '-t', '--tenant',
        required=True,
        type=valid_uuid,
        help="Openmano tenant uuid to use",
        )

    subparsers = parser.add_subparsers(dest='command', help='openmano commands')

    vnf_create_parser = subparsers.add_parser(
            'vnf-create',
            help="Adds a openmano vnf into the catalog"
            )
    vnf_create_parser.add_argument(
            "file",
            help="location of the JSON file describing the VNF",
            type=argparse.FileType('rb'),
            )

    vnf_delete_parser = subparsers.add_parser(
            'vnf-delete',
            help="Deletes a openmano vnf into the catalog"
            )
    vnf_delete_parser.add_argument(
            "uuid",
            help="The vnf to delete",
            type=valid_uuid,
            )

    _ = subparsers.add_parser(
            'vnf-list',
            help="List all the openmano VNFs in the catalog",
            )

    ns_create_parser = subparsers.add_parser(
            'scenario-create',
            help="Adds a openmano ns scenario into the catalog"
            )
    ns_create_parser.add_argument(
            "file",
            help="location of the JSON file describing the NS",
            type=argparse.FileType('rb'),
            )

    ns_delete_parser = subparsers.add_parser(
            'scenario-delete',
            help="Deletes a openmano ns into the catalog"
            )
    ns_delete_parser.add_argument(
            "uuid",
            help="The ns to delete",
            type=valid_uuid,
            )

    _ = subparsers.add_parser(
            'scenario-list',
            help="List all the openmano scenarios in the catalog",
            )

    ns_instance_create_parser = subparsers.add_parser(
            'scenario-deploy',
            help="Deploys a openmano ns scenario into the catalog"
            )
    ns_instance_create_parser.add_argument(
            "scenario_name",
            help="The ns scenario name to deploy",
            )
    ns_instance_create_parser.add_argument(
            "instance_name",
            help="The ns instance name to deploy",
            )


    ns_instance_delete_parser = subparsers.add_parser(
            'instance-scenario-delete',
            help="Deploys a openmano ns scenario into the catalog"
            )
    ns_instance_delete_parser.add_argument(
            "instance_name",
            help="The ns instance name to delete",
            )


    _ = subparsers.add_parser(
            'instance-scenario-list',
            help="List all the openmano scenario instances in the catalog",
            )

    _ = subparsers.add_parser(
            'datacenter-list',
            help="List all the openmano datacenters",
            )

    args = parser.parse_args(argv)

    return args


def main():
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("openmano_client.py")

    if "RIFT_INSTALL" not in os.environ:
        logger.error("Must be in rift-shell to run.")
        sys.exit(1)

    args = parse_args()
    openmano_cli = OpenmanoCliAPI(logger, args.host, args.port, args.tenant)

    if args.command == "vnf-create":
        openmano_cli.vnf_create(args.file.read())

    elif args.command == "vnf-delete":
        openmano_cli.vnf_delete(args.uuid)

    elif args.command == "vnf-list":
        for uuid, name in openmano_cli.vnf_list().items():
            print("{} {}".format(uuid, name))

    elif args.command == "scenario-create":
        openmano_cli.ns_create(args.file.read())

    elif args.command == "scenario-delete":
        openmano_cli.ns_delete(args.uuid)

    elif args.command == "scenario-list":
        for uuid, name in openmano_cli.ns_list().items():
            print("{} {}".format(uuid, name))

    elif args.command == "scenario-deploy":
        openmano_cli.ns_instantiate(args.scenario_name, args.instance_name)

    elif args.command == "instance-scenario-delete":
        openmano_cli.ns_terminate(args.instance_name)

    elif args.command == "instance-scenario-list":
        for uuid, name in openmano_cli.ns_instance_list().items():
            print("{} {}".format(uuid, name))

    elif args.command == "datacenter-list":
        for uuid, name in openmano_cli.datacenter_list():
            print("{} {}".format(uuid, name))

    else:
        logger.error("Unknown command: %s", args.command)
        sys.exit(1)

if __name__ == "__main__":
    main()
