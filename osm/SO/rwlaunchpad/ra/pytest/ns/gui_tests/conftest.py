#!/usr/bin/env python
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
import pytest
import os
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

gi.require_version('RwCloudYang', '1.0')
gi.require_version('RwConfigAgentYang', '1.0')
gi.require_version('RwSdnYang', '1.0')

from gi.repository import (
    RwSdnYang,
    RwCloudYang,
    RwConfigAgentYang,
)

gi.require_version('RwKeyspec', '1.0')
from gi.repository.RwKeyspec import quoted_key


@pytest.fixture(scope='session')
def cloud_proxy(mgmt_session):
    """cloud_proxy."""
    return mgmt_session.proxy(RwCloudYang)


@pytest.fixture(scope='session')
def sdn_proxy(mgmt_session):
    """sdn_proxy."""
    return mgmt_session.proxy(RwSdnYang)


@pytest.fixture(scope='session')
def config_agent_proxy(mgmt_session):
    """config_agent_proxy."""
    return mgmt_session.proxy(RwConfigAgentYang)


@pytest.fixture(scope='session')
def driver(request, confd_host, logger):
    """Set up virtual diplay and browser driver."""
    # Set up the virtual display
    display = Display(visible=0, size=(1024, 768))
    display.start()

    logger.info("Initializing the chrome web driver")
    root_dir = os.environ.get('RIFT_ROOT')
    webdriver_path = '{}/chromedriver'.format(root_dir)
    # webdriver_path = os.environ["webdriver.chrome.driver"]
    # Something like this should be implemented.

    driver_ = webdriver.Chrome(executable_path=webdriver_path)
    driver_.implicitly_wait(5)
    url = "http://{}:8000/".format(confd_host)
    logger.info("Getting the URL {}".format(url))
    driver_.get(url)
    WebDriverWait(driver_, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "logo"))
    )

    logger.info("Signing into the Rift home page")
    driver_.find_element_by_name("username").send_keys("admin")
    driver_.find_element_by_name("password").send_keys("admin")
    driver_.find_element_by_id("submit").click()
    WebDriverWait(driver_, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "skyquakeNav"))
    )

    def teardown():
        driver_.quit()
        display.stop()

    yield driver_
