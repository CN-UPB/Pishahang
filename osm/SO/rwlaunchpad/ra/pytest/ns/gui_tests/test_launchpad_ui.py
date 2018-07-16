#!/usr/bin/env python
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


import gi

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


gi.require_version('RwUserYang', '1.0')
gi.require_version('RwProjectYang', '1.0')
gi.require_version('RwConmanYang', '1.0')

from gi.repository import (
    RwUserYang,
    RwProjectYang,
    RwConmanYang
)

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


class TestGUI(object):
    """TestGUI."""

    def click_element_and_wait(self, driver, key_word, wait=True):
        """Click and wait for that element to appear."""
        path = "//a[text()={}]".format(quoted_key(key_word))
        driver.find_element_by_xpath(path).click()
        if wait is True:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((
                    By.XPATH, path)))

    def click_button(self, driver, key_word):
        """Click a button."""
        path = "//div[text()={}]".format(quoted_key(key_word))
        driver.find_element_by_xpath(path).click()

    def input_value(self, driver, data_reactid, value):
        """Input values to field."""
        path = "//input[@data-reactid={}]".format(quoted_key(data_reactid))
        driver.find_element_by_xpath(path).send_keys(value)

    def test_basic_checks(
            self, driver, logger, rw_project_proxy, rw_user_proxy):
        """test_basic_checks."""
        logger.debug('Check access to all basic pages.')
        basic_pages = (
            ['Accounts', 'Catalog', 'Launchpad', 'ADMINISTRATION',
             'PROJECT: default', 'admin'])
        for key_word in basic_pages:
            self.click_element_and_wait(driver, key_word)

        logger.debug('Create a test project.')
        self.click_element_and_wait(driver, 'ADMINISTRATION')
        self.click_element_and_wait(driver, 'Project Management', wait=False)
        self.click_button(driver, 'Add Project')
        self.input_value(driver, '.0.4.0.1.0.4.0.0.1.0.1', 'test_project')
        self.click_button(driver, 'Create')

        logger.debug('Verify test project is created in ui.')
        path = "//div[text()={}]".format(quoted_key('test_project'))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, path)))

        logger.debug('Verify test project is created in config.')
        project_cm_config_xpath = '/project[name={}]/project-state'
        project_ = rw_project_proxy.get_config(
            project_cm_config_xpath.format(
                quoted_key('test_project')), list_obj=True)
        assert project_

        logger.debug('Create a test user.')
        self.click_element_and_wait(driver, 'ADMINISTRATION')
        self.click_element_and_wait(driver, 'User Management', wait=False)
        self.click_button(driver, 'Add User')
        self.input_value(driver, '.0.4.0.1.1.0.4.0.0.1.0.1', 'test_user')
        self.input_value(driver, '.0.4.0.1.1.0.4.0.3.1.0.1', 'mypasswd')
        self.input_value(driver, '.0.4.0.1.1.0.4.0.3.1.1.1', 'mypasswd')
        self.click_button(driver, 'Create')

        logger.debug('Verify test user is created in ui.')
        path = "//div[text()={}]".format(quoted_key('test_user'))
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((
                By.XPATH, path)))

        logger.debug('Verify test user is created in config.')
        user_config_xpath = (
            '/user-config/user[user-name={user_name}][user-domain={domain}]')
        user_ = rw_user_proxy.get_config(
            user_config_xpath.format(
                user_name=quoted_key('test_user'),
                domain=quoted_key('system')))
        assert user_
