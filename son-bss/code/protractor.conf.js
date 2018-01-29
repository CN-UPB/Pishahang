/**
 * Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
 * ALL RIGHTS RESERVED.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *     http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 * 
 * Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
 * nor the names of its contributors may be used to endorse or promote 
 * products derived from this software without specific prior written 
 * permission.
 * 
 * This work has been performed in the framework of the SONATA project,
 * funded by the European Commission under Grant number 671517 through 
 * the Horizon 2020 and 5G-PPP programmes. The authors would like to 
 * acknowledge the contributions of their colleagues of the SONATA 
 * partner consortium (www.sonata-nfv.eu).* dirPagination - AngularJS module for paginating (almost) anything.
 */

var HtmlScreenshotReporter = require('protractor-jasmine2-html-reporter');

var reportName;

exports.config = {
  seleniumAddress: 'http://localhost:4444/wd/hub',  
  seleniumServerJar: './node_modules/protractor/selenium/selenium-server-standalone-2.52.0.jar',    
  //specs: ['E2E_tests/todo-spec.js'],
  suites: {
	  unitTests: ['E2E_tests/menusNavigation.js', 'E2E_tests/serviceInstantiation.js', 'E2E_tests/serviceUpdate.js', 'E2E_tests/serviceLicenseUpdate.js', 'E2E_tests/licenseStore.js', 'E2E_tests/serviceStop.js'],	  
	  menus_Navigation: ['E2E_tests/menusNavigation.js'],
	  service_Instantiation: ['E2E_tests/serviceInstantiation.js'],
	  service_Update: ['E2E_tests/serviceUpdate.js'],
	  service_Instantiation_E2E: ['E2E_tests/serviceInstantiationE2E.js'],
    service_License_Update: ['E2E_tests/serviceLicenseUpdate.js'],
    license_store: ['E2E_tests/licenseStore.js'],
    service_Stop: ['E2E_tests/serviceStop.js']    
  },
  
  capabilities: {
  'browserName': 'phantomjs',
    version: '',
    platform: 'ANY',
	  'phantomjs.binary.path': './node_modules/phantomjs-prebuilt/bin/phantomjs',
    'phantomjs.cli.args': ['--web-security=false', '--ignore-ssl-errors=true']
  },
     
  
  onPrepare: function() {
     process.argv.forEach((val, index, array) => {
        if (`${val}`=='--suite') {
                reportName = process.argv[`${index+1}`];
        }
     });    
     jasmine.getEnv().addReporter(
        new HtmlScreenshotReporter({
          savePath: 'E2E_tests/reports/',
          filePrefix: reportName
        })
     );
   }
}