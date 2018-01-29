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
 
describe('SonataBSS Instantiates a Service', function() {

    var requestId;
	
    beforeEach(function() {
        browser.driver.manage().window().maximize();
        browser.get(browser.params.protocol+'://'+browser.params.hostname+':1337/#/login');
        browser.driver.findElement(by.id('username')).sendKeys('sonata');
        browser.driver.findElement(by.id('password')).sendKeys('sonata');
        browser.driver.findElement(by.xpath('//button[. = "Login"]')).click();
        browser.driver.findElement(by.xpath("//a[@href='#/nSDs']")).click();
    });


    it('services list must not be empty', function() {
        var count = element.all(by.repeater('nSD in nSDs')).count();
        expect(count).toBeGreaterThan(0);
    });

    it('location and nap inputs', function() {

        var EC = protractor.ExpectedConditions;

        var modal = element.all(by.css('[ng-click="openInstantiateNSD(nSD)"]')).get(0).click();
        browser.wait(EC.visibilityOf(modal), 5000);        
        
        modal = element(by.id('instantiateNSD'));
        
        element.all(by.repeater('ingress in ingresses')).each(function(elem) {
            elem.element(by.model("ingress.location")).sendKeys('Aveiro');
            elem.element(by.model("ingress.nap")).sendKeys('10.10.0.0/16');
        }); 

        element.all(by.repeater('egress in egresses')).each(function(elem) {
            elem.element(by.model("egress.location")).sendKeys('London');
            elem.element(by.model("egress.nap")).sendKeys('20.20.0.0/16');
        });

        var yes = modal.element(by.id('yesButton'));
        expect(yes.isEnabled()).toBe(true);

    });

    it('when clicked: "request service instantiation" instantiates a new service', function() {

        var EC = protractor.ExpectedConditions;

        var modal = element.all(by.css('[ng-click="openInstantiateNSD(nSD)"]')).get(0).click();
        browser.wait(EC.visibilityOf(modal), 5000);

        modal = element(by.id('instantiateNSD'));
        var yes = modal.element(by.id('yesButton'));
        yes.click();
        browser.sleep(1500);

        modal = element(by.id('instantiateRequest'));
        expect(modal.isDisplayed()).toBe(true); 


        modal.element(by.id('requestId')).getText().then(function(text) {
            requestId = text;            
        });

    });

    it('instantiation request must be in the list', function() {

        browser.driver.findElement(by.xpath("//a[@href='#/requests']")).click();        
        
        var query = element(by.model('RequestsSearch'));
        query.sendKeys(requestId);

        var data = element.all(by.repeater("Request in Requests"));

        expect(data.count()).toBe(1);

    });

	it('request must be ready after service instantiation process', function() {

		browser.driver.findElement(by.xpath("//a[@href='#/requests']")).click();

		var query = element(by.model('RequestsSearch'));
		query.sendKeys(requestId);

		var EC = protractor.ExpectedConditions;
		browser.wait(EC.textToBePresentInElement(element(by.repeater("Request in Requests").column('status')) ,'ready', 60000));

    });

});