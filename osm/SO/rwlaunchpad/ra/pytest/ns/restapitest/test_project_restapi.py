# !/usr/bin/env python
"""
#
#   Copyright 2017 RIFT.io Inc
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

@author Anoop Valluthadam (anoop.valluthadam@riftio.com), Vishnu Narayanan K.A
@brief Create/Delete/Other operations of Projects and User
"""

import os

from utils.imports import * # noqa
from utils.traversal_engine import traverse_it
from utils.utils import parse_input_data
from utils.tbac_token_utils import * # noqa

headers = {'content-type': 'application/json'}


class TestRestAPI(object):
    """TestRestAPI."""

    def traverse_and_find_all_keys(self, it, key_dict):
        """Find all keys and their data types present in the json schema.

        Args:
            it (dict): the json
            key_dict (dict): will be populated with the keys & their datatypes
        Returns:
            key_dict (dict): will be populated with the keys & their datatypes
        """
        if (isinstance(it, list)):
            for item in it:
                self.traverse_and_find_all_keys(item, key_dict)
            return key_dict

        elif (isinstance(it, dict)):
            for key in it.keys():
                if key == 'name' and 'data-type' in it:
                    if isinstance(it['data-type'], dict):
                        dtype = next(iter(it['data-type']))
                        if ((it[key] in key_dict) and
                                (dtype not in key_dict[it[key]])):

                            key_dict[it[key]].append(dtype)

                        elif it[key] not in key_dict:
                            key_dict[it[key]] = [dtype]
                        else:
                            pass
                    else:
                        if ((it[key] in key_dict) and
                                (it['data-type'] not in key_dict[it[key]])):

                            key_dict[it[key]].append(it['data-type'])

                        elif it[key] not in key_dict:
                            key_dict[it[key]] = [it['data-type']]
                        else:
                            pass
                self.traverse_and_find_all_keys(it[key], key_dict)
            return key_dict
        else:
            return None

    def create_post_call(
            self, data, confd_host, url, logger, state, number_of_tests):
        """Create the POST.

        Args:
            data (dict): JSON data
            confd_host (string): IP addr of the Launchpad
            url (string): the url for the post call
            logger (logger Object): log object
            state: for the tbac token
            number_of_tests (list): test & error cases count
        Returns:
            number_of_tests (list): test & error cases count
        Raises:
            requests.exceptions.ConnectionError: in case we loose connection
            from the Launchpad, mostly when Launchpad crashes

        """
        number_of_tests[0] += 1

        key = next(iter(data))
        if 'project' in url:
            name = str(data[key][0]["name"])
            new_url = url + name
        elif 'user-config' in url:
            name = str(data[key]['user'][0]['user-name'])
            domain = str(data[key]['user'][0]['user-domain'])
            data = data['rw-user:user-config']
            new_url = url + '/user/' + name + ',' + domain
        else:
            raise Exception('Something wrong with the URL')

        logger.debug(data)
        headers['Authorization'] = 'Bearer ' + state.access_token
        try:
            create_result = state.session.post(
                url, data=json.dumps(data),
                headers=headers, verify=False)
            get_result = state.session.get(
                new_url,
                headers=headers, verify=False)
            delete_result = state.session.delete(
                new_url,
                headers=headers, verify=False)
        except requests.exceptions.ConnectionError:
            logger.error('Crashed for the data: \n{}'.format(data))
            number_of_tests[1] += 1
            exit(1)

        logger.debug(
            'create result:\n{}\n{}\n'.format(
                create_result.status_code, create_result.text))
        logger.debug(
            'get result:\n{}\n{}\n'.format(
                get_result.status_code, get_result.text))
        logger.debug(
            'delete result:\n{}\n{}\n'.format(
                delete_result.status_code, delete_result.text))

        return number_of_tests

    def get_schema(self, confd_host, url, property_=None):
        """Get schema.

        Args:
            confd_host (string): Launchpad IP
            property_ (string): vnfd/nsd/user etc
        Returns:
            schema (JSON): Schema in JSON format
        """
        headers = {'content-type': 'application/json'}

        result = requests.get(url, auth=HTTPBasicAuth('admin', 'admin'),
                              headers=headers, verify=False)

        schema = json.loads(result.text)

        return schema

    def traverse_call(
            self, test_input, data, k_dict, confd_host, logger,
            number_of_tests, depth, url, state):
        """Traversing through the values from the test IP JSON.

        Args:
            test_input (string): the data from the test IP JSON
            data (json): schema data
            k_dict (dict): dictionary of the JSON IP
            confd_host (string): Launchpad IP
            logger (logger obj): log object
            number_of_tests (list): test & error cases count
            depth (int): depth of the json
            url (string): the url for the post call
            state: for the tbac token
        Returns:
            number_of_tests (list): test & error cases count
        """
        for key, kdata_types in k_dict.items():
            for kdata_type in kdata_types:
                if kdata_type in test_input:
                    test_values = test_input[kdata_type]
                    for test_value in test_values:
                        test_data = {kdata_type: test_value}
                        # Actual traversal call which will generate data
                        json_data = traverse_it(
                            data, original=False,
                            test_value=test_data, test_key=key,
                            max_depth=depth)

                        number_of_tests = self.create_post_call(
                            json_data, confd_host, url,
                            logger, state, number_of_tests)

        return number_of_tests

    def test_get_token(
            self, rw_user_proxy, rbac_user_passwd, user_domain,
            rbac_platform_proxy, rw_rbac_int_proxy, mgmt_session, state):
        """Setting the public key in config and get token."""
        client_id = '1234'
        rift.auto.mano.create_user(
            rw_user_proxy, 'test', rbac_user_passwd, user_domain)
        rift.auto.mano.assign_platform_role_to_user(
            rbac_platform_proxy, 'rw-rbac-platform:super-admin', 'test',
            user_domain, rw_rbac_int_proxy)
        openidc_xpath = (
            '/rw-openidc-provider:openidc-provider-config/' +
            'rw-openidc-provider:openidc-client' +
            '[rw-openidc-provider:client-id={}]'.format(quoted_key(client_id))
        )
        config_object = (
            RwOpenidcProviderYang.
            YangData_RwOpenidcProvider_OpenidcProviderConfig_OpenidcClient.
            from_dict({
                'client_id': client_id,
                'client_name': 'test',
                'user_name': 'test',
                'user_domain': 'tbacdomain',
                'public_key': PUBLIC_KEY}))
        rw_open_idc_proxy = mgmt_session.proxy(RwOpenidcProviderYang)
        rw_open_idc_proxy.create_config(openidc_xpath, config_object)

        # Get the token
        jwt = Jwt(private_key=PRIVATE_KEY, iss=client_id,
                  sub="test", aud="https://locahost:8009")
        jws = jwt.sign_jwt()
        body_tuple = (
            ("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer"),
            ("assertion", jws),
        )

        req = tornado.httpclient.HTTPRequest(
            url=TOKEN_URL,
            method='POST',
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            ca_certs=state.cert,
            body=urllib.parse.urlencode(body_tuple)
        )
        client = tornado.httpclient.HTTPClient()
        resp = client.fetch(req)
        token_resp = json.loads(resp.body.decode('utf-8'))
        assert "access_token" in token_resp
        state.access_token = token_resp["access_token"]

        auth_value = 'Bearer ' + state.access_token
        state.session = requests.Session()
        state.session.headers.update({
            'content-type': 'application/json',
            'Authorization': auth_value
        })

    def test_user_restapi(self, confd_host, logger, state):
        """Test user creation restapi."""
        rift_install = os.getenv('RIFT_INSTALL')
        file_path = (
            '{}/usr/rift/systemtest/pytest/'.format(rift_install) +
            'system/ns/restapitest/test_inputs/test_inputs.json')
        test_input = parse_input_data(file_path)
        schema_url_for_user = (
            "https://{}:8008/v2/api/schema/user-config/".format(confd_host)
        )
        url_for_user = (
            "https://{}:8008/v2/api/config/user-config".format(confd_host)
        )
        data = self.get_schema(confd_host, schema_url_for_user)

        key_dict = {}
        k_dict = self.traverse_and_find_all_keys(data, key_dict)

        number_of_tests = [0, 0]  # [total no. of tests, no. of erros]
        # Traverse with depth but with out any specific key
        for depth in range(14, 15):
                number_of_tests = self.traverse_call(
                    test_input, data["user-config"], k_dict, confd_host,
                    logger, number_of_tests, depth, url_for_user, state)
        logger.debug(
            'No of tests ran for userapi: {}'.format(number_of_tests[0]))
        logger.debug(
            'No of crashed tests for userapi:{}'.format(number_of_tests[1]))

    def test_project_restapi(self, confd_host, logger, state):
        """Test project creation restapi."""
        rift_install = os.getenv('RIFT_INSTALL')
        file_path = (
            '{}/usr/rift/systemtest/pytest/'.format(rift_install) +
            'system/ns/restapitest/test_inputs/test_inputs.json')
        test_input = parse_input_data(file_path)

        schema_url_for_project = (
            "https://{}:8008/v2/api/schema/project/".format(confd_host)
        )
        url_for_project = (
            "https://{}:8008/v2/api/config/project/".format(confd_host)
        )
        data = self.get_schema(confd_host, schema_url_for_project)

        key_dict = {}
        k_dict = self.traverse_and_find_all_keys(data, key_dict)

        number_of_tests = [0, 0]  # [total no. of tests, no. of erros]

        # Traverse with depth but with out any specific key
        for depth in range(5, 6):
                number_of_tests = self.traverse_call(
                    test_input, data["project"], k_dict, confd_host,
                    logger, number_of_tests, depth, url_for_project, state)
        logger.debug(
            'No of tests ran for projectapi: {}'.format(number_of_tests[0]))
        logger.debug(
            'No of crashed tests for projectapi:{}'.format(number_of_tests[1]))
