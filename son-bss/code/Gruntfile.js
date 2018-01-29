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

 var isAuthorizedUser = function (req, validUsername) {

	var jwt = require('jsonwebtoken');
	var bearer = "Bearer ";
	var token = req.headers.authorization.substring(bearer.length);	
	var decoded = jwt.decode(token);
	
	if ((decoded != null) && (validUsername === decoded.name)) {
		return true;
	} else {
		return false;
	}
}

var fmock = function (req, res, next) {	

	//var Base64 = require('js-base64').Base64;

	var authorizedUser = {
		"username": "sonata",
		"password": "sonata"
	};
	var notAuthorizedUser = {
		"username": "test",
		"password": "test"
	};
	var AuthorizedUser = false;

	//console.log("Mock: receiving "+req.method+" request");
	if (req.url.indexOf('/mock') === 0) {

		// everything after /mock is the path that we need to mock
		var path = req.url.substring(5);
		var body = '';

		res.setHeader('Access-Control-Allow-Origin', '*');
		res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, DELETE, PUT, PATCH');
		res.setHeader('Access-Control-Allow-Headers', 'Authorization, Origin, X-Requested-With, Content-Type, Accept');
		res.setHeader('Access-Control-Expose-Headers', 'Link, X-Total-Count');	

		switch (req.method) {
		case 'OPTIONS':
			//console.log('OPTIONS...');
			res.writeHeader(200, {
				"Content-Type": "application/json"
			});
			res.end();
			break;
		case 'POST':
			//console.log('POST...');
			//login
			switch (true) {
				case /^\/sessions/.test(path):
					body = "";
					req.on('data', function (data) {
						body += data;
					});
					req.on('end', function () {
						var params = JSON.parse(body);

						if (params.username === authorizedUser.username && params.password === authorizedUser.password) {
							//console.log("Authenticated and Authorizated usr");
							body = '{"token": {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6InNvbmF0YSIsImFkbWluIjp0cnVlfQ.AdgPchW4kBolbrVPn8YlrNIOx8XqcHcO_bCR2gclGyo"}, "user_role": "customer"}';
							res.writeHeader(200, {
								"Content-Type": "application/json"
							});						
						} else {
							if (params.username === notAuthorizedUser.username && params.password === notAuthorizedUser.password) {
								// not AuthorizedUser: user is authenticated but token doesn't allow it to retrieve platform information
								//console.log("Authenticated but not Authorizated usr");
								body = '{"token": {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6InRlc3QiLCJhZG1pbiI6ZmFsc2V9.ysMOZXnPs4VXMhgwhJmSPWjKW2trpjA8Ym-X4plfVrY"}}';
								res.writeHeader(200, {
									"Content-Type": "application/json"
								});							
							} else {
								//console.log("not valid usr/pwd");							
								body = '{"code": "401", "message":"Not valid user/password"}';
								res.writeHeader(401);							
							}
						}
						res.write(body);
						res.end();
					});
					break;
				case /^\/users/.test(path):
					// registering
					body = "";
					req.on('data', function (data) {
						body += data;
					});
					req.on('end', function () {
						var params = JSON.parse(body);

						if (params.username === authorizedUser.username) {
								res.writeHeader(200, {
									"Content-Type": "application/json"
								});							
							} else {
								//console.log("not valid usr/pwd");							
								body = '{"code": "401", "message":"Not valid user/password"}';
								res.writeHeader(401);							
							}
						res.write(body);
						res.end();											
					});
					break;
				default:								
					if (isAuthorizedUser(req, authorizedUser.username) === false) {
						body = '{"code": "401", "message":"Not Authorized User"}';
						res.writeHeader(401);
					} else {
						body += '{"id":"1c58b169-7c38-4bcd-9421-a91bd786f100","created_at":"2017-12-01T09:00:44.495Z","updated_at":"2017-12-01T09:00:44.495Z","service_uuid":"456fd81b-2fd2-4dc6-b7d6-cbd84c43abb5","status":"NEW","request_type":"CREATE","service_instance_uuid":null,"began_at":"2017-12-01T09:00:44.494Z","callback":"http://sp.int3.sonata-nfv.eu:5400/service-instantiation-time"}';
						res.writeHeader(200, {
							"Content-Type": "application/json"
						});
					}
					res.write(body);
					res.end();
					break;				
			}
			break;
		case 'GET':
			//console.log('GET...');
			if (isAuthorizedUser(req, authorizedUser.username) === false) {					
				body = '{"code": "401", "message":"Not Authorized User"}';
				res.writeHeader(401);
			} else {
				switch (true){
					case /^\/services/.test(path):
						if (path.indexOf('/services?status=active') === 0) {
							//console.log("GET /services");
							//body response
							body += JSON.stringify(require('./examples/activeNSD.json'));
							//body response
							//res.setHeader('Access-Control-Allow-Origin', '*');
							res.writeHeader(200, {
								"Content-Type": "application/json",
								"Link": "<http://localhost:1338/mock/services?offset=0&limit=10>; rel=\"first\",<http://localhost:1338/mock/services?offset=0&limit=10>; rel=\"last\"",
							});
							//res.writeHead['content-type'] = 'application/json';
						} else {
							//console.log("GET /services");
							//body response
							body += JSON.stringify(require('./examples/allNSD.json'));
							//body response
							//res.setHeader('Access-Control-Allow-Origin', '*');
							res.writeHeader(200, {
								"Content-Type": "application/json",
								"Link": "<http://localhost:1338/mock/services?offset=0&limit=10>; rel=\"first\",<http://localhost:1338/mock/services?offset=0&limit=10>; rel=\"last\"",
							});
							//res.writeHead['content-type'] = 'application/json';
						};
						break;
					case /^\/requests/.test(path):
						if (path.indexOf('/requests?limit=10&offset=1') === 0) {
						    body += JSON.stringify(require('./examples/request2.json'));							
							res.writeHeader(200, {
								"Content-Type": "application/json",
								"Link": "<http://localhost:1338/mock/requests?limit=10&offset=2>; rel=\"first\",<http://localhost:1338/mock/requests?limit=10&offset=3>; rel=\"last\""
							});
						} else {
							if (path.indexOf('/requests?limit=10&offset=2') === 0) {
								body += JSON.stringify(require('./examples/request3.json'));							
								res.writeHeader(200, {
									"Content-Type": "application/json",
									"Link": "<http://localhost:1338/mock/requests?limit=10&offset=3>; rel=\"first\",<http://localhost:1338/mock/requests?limit=10&offset=3>; rel=\"last\""
								});
							} else {
								if (path.indexOf('/requests?limit=10&offset=3') === 0) {
									body += JSON.stringify(require('./examples/request4.json'));							
									res.writeHeader(200, {
										"Content-Type": "application/json",
										"Link": "<http://localhost:1338/mock/requests?limit=10&offset=3>; rel=\"first\",<http://localhost:1338/mock/requests?limit=10&offset=3>; rel=\"last\""
									});
								} else {
									body += JSON.stringify(require('./examples/request.json'));							
									res.writeHeader(200, {
										"Content-Type": "application/json",
										"Link": "<http://localhost:1338/mock/requests?limit=10&offset=1>; rel=\"first\",<http://localhost:1338/mock/requests?limit=10&offset=3>; rel=\"last\""
									});
								}	
							}
						}
						break;
					case /^\/records\/services/.test(path):
						if (path.indexOf('/records/services?limit=10&offset=1') === 0) {
							body += JSON.stringify(require('./examples/NSR2.json'));							
							res.writeHeader(200, {
								"Content-Type": "application/json",
								"Link": "<http://localhost:1338/mock/records/services?limit=10&offset=1>; rel=\"first\",<http://localhost:1338/mock/records/services?limit=10&offset=1>; rel=\"last\"",
							});
						} else {
							body += JSON.stringify(require('./examples/NSR.json'));							
							res.writeHeader(200, {
								"Content-Type": "application/json",
								"Link": "<http://localhost:1338/mock/records/services?limit=10&offset=1>; rel=\"first\",<http://localhost:1338/mock/records/services?limit=10&offset=1>; rel=\"last\"",
							});
						}
						break;
					case /^\/licences/.test(path):
						body += JSON.stringify(require('./examples/userLicenses.json'));
						res.writeHeader(200, {
							"Content-Type": "application/json",
							"Link": "<http://localhost:1338/mock/licenses/user/1234?limit=10&offset=0>; rel=\"first\",<http://localhost:1338/mock/licenses/user/1234?limit=10&offset=0>; rel=\"last\""
						});							
						break;
					case /^\/vims/.test(path):
						if (path.indexOf('/vims/') === 0) {
							if (path.indexOf('/vims/e3de42b8-3d62-42c8-a5b6-a92089ed4a61') === 0) {
								body += JSON.stringify(require('./examples/vimsList.json'));
							}
						} else {
							body += JSON.stringify(require('./examples/vimRequests.json'));
						}
						res.writeHeader(200, {
							"Content-Type": "application/json",
							"Link": "<http://localhost:1338/mock/vims/1234?limit=10&offset=0>; rel=\"first\",<http://localhost:1338/mock/xxx?limit=10&offset=0>; rel=\"last\""
						})
						break;
					default:
						res.writeHeader(200, {
							"Content-Type": "application/json",
							"Link": "<http://localhost:1338/mock/xxx?limit=10&offset=0>; rel=\"first\",<http://localhost:1338/mock/xxx?limit=10&offset=0>; rel=\"last\"",
						});
						break;
				}
			}
			res.write(body);
			res.end();
			break;
		case 'PUT':
			//console.log('PUT...');
			if (isAuthorizedUser(req, authorizedUser.username) === false) {				
				body = '{"code": "401", "message":"Not Authorized User"}';
				res.writeHeader(401);
			} else {
				res.writeHeader(200, {
					"Content-Type": "application/json"
				});
			}
			res.write(body);
			res.end();
			break;
		case 'DELETE':
			//console.log('DELETE...');
			if (path.indexOf('/sessions') === 0) {
				res.writeHeader(200, {
					"Content-Type": "application/json"
				});
				res.write(body);
				res.end();
			}
			break;
		case 'PATCH':
			if (path.indexOf('/records/services') === 0) {
				res.writeHeader(200, {
					"Content-Type": "application/json"
				});
				res.write(body);
				res.end();
			}
			break;
		}
	}
};

module.exports = function(grunt) {

	grunt.initConfig({
		pkg: grunt.file.readJSON('package.json'),
		watch: {
			options: {
				livereload: true
        	},      
        	protractor: {        
        		files: ['E2E_tests/todo*.js'],
        		tasks: ['protractor:run']
        	}
        },
        ngconstant: {
			// Options for all targets
			options: {
				space: '  ',
				wrap: '"use strict";\n\n {%= __ngModule %}',
				name: 'config',
				livereload: true
			},
		  // Environment targets
		  development: {
		  	options: {
		  		dest: 'app/config/config.js'
		  	},
		  	constants: {
		  		ENV: {
		  			name: 'development',
		  			apiEndpoint: [grunt.option('gkApiUrl')],
		  			userManagementEnabled: [grunt.option('userManagementEnabled')],
		  			licenseManagementEnabled: [grunt.option('licenseManagementEnabled')]
		  		}
		  	}
		  },
		  integration: {
		  	options: {
		  		dest: 'app/config/config.js'
		  	},
		  	constants: {
		  		ENV: {
		  			name: 'integration',
		  			apiEndpoint: [grunt.option('gkApiUrl')],
		  			userManagementEnabled: [grunt.option('userManagementEnabled')],
		  			licenseManagementEnabled: [grunt.option('licenseManagementEnabled')]
		  		}
		  	}
		  },
		  qualification: {
		  	options: {
		  		dest: 'app/config/config.js'
		  	},
		  	constants: {
		  		ENV: {
		  			name: 'qualification',
		  			apiEndpoint: [grunt.option('gkApiUrl')],
		  			userManagementEnabled: [grunt.option('userManagementEnabled')],
		  			licenseManagementEnabled: [grunt.option('licenseManagementEnabled')]
		  		}
		  	}
		  }
		},
		connect: {			
			dist: {				
				options: (function() { 
					if ( !grunt.option( 'protocol' ) ) {   						
    					grunt.option( 'protocol', 'http' );
  					}
  					if ( !grunt.option( 'hostname' ) ) {   						
    					grunt.option( 'hostname', 'localhost' );
  					}
    				if (grunt.option('protocol')=='https') {
      					return {
      						protocol: 'https',
							key: grunt.file.read('app/certs/sonata.key').toString(),
							cert: grunt.file.read('app/certs/sonata.crt').toString(),
							hostname: grunt.option('hostname'),
							open: true,					
							port: 1337,
							base: 'app'	
      					};
    				} else {
      					return {
							protocol: 'http',
							hostname: grunt.option('hostname'),
							open: true,					
							port: 1337,
							base: 'app'
      					};
    				}
  				}())
			},
			mock: {
				options: (function() { 
					if ( !grunt.option( 'protocol' ) ) {   						
    					grunt.option( 'protocol', 'http' );
  					}
  					if ( !grunt.option( 'hostname' ) ) {   						
    					grunt.option( 'hostname', 'localhost' );
  					}
    				if (grunt.option('protocol')=='https') {
      					return {
      						protocol: 'https',
							key: grunt.file.read('app/certs/sonata.key').toString(),
							cert: grunt.file.read('app/certs/sonata.crt').toString(),
							hostname: grunt.option('hostname'),
							port: 1338,
							base: 'app',
							middleware: [
							fmock
							],	
      					};
    				} else {
      					return {
							protocol: 'http',
							hostname: grunt.option('hostname'),
							port: 1338,
							base: 'app',
							middleware: [
							fmock
							],
      					};
    				}
  				}())
			},									
			int: {
				options: (function() { 
					if ( !grunt.option( 'protocol' ) ) {   						
    					grunt.option( 'protocol', 'http' );
  					}
  					if ( !grunt.option( 'hostname' ) ) {   						
    					grunt.option( 'hostname', 'localhost' );
  					}
    				if (grunt.option('protocol')=='https') {
      					return {
      						protocol: 'https',
							key: grunt.file.read('app/certs/sonata.key').toString(),
							cert: grunt.file.read('app/certs/sonata.crt').toString(),
							hostname: grunt.option('hostname'),
							port: 1337,
							base: 'app'	
      					};
    				} else {
      					return {
							protocol: 'http',
							hostname: grunt.option('hostname'),
							port: 1337,
							base: 'app'
      					};
    				}
  				}())				
			},
			qualif: (function() { 
				if ( !grunt.option( 'protocol' ) ) {   						
    				grunt.option( 'protocol', 'http' );
  				}
  				if ( !grunt.option( 'hostname' ) ) {   						
    				grunt.option( 'hostname', 'localhost' );
  				}
    			if (grunt.option('protocol')=='https') {
      				return {
      					protocol: 'https',
						key: grunt.file.read('app/certs/sonata.key').toString(),
						cert: grunt.file.read('app/certs/sonata.crt').toString(),
						hostname: grunt.option('hostname'),
						port: 1337,
						base: 'app'	
      				};
    			} else {
      				return {
						protocol: 'http',
						hostname: grunt.option('hostname'),
						port: 1337,
						base: 'app'
      				};
    			}
  			}())
		},
		protractor: {
			options: {
				configFile: "protractor.conf.js",		 
				noColor: false,
				keepAlive: true,
				args: {
					params: {
						hostname: [grunt.option('hostname')],
						protocol: [grunt.option('protocol')]
					}
				}
			},		  
			run: {},
			auto: {
				keepAlive: true,
				options: {
					args: {
						seleniumPort: 4444			
					}
				}
			}
		},
		protractor_webdriver: {
			start: {
				options: {
					path: './node_modules/protractor/bin/',
					keepAlive: true,
					command: 'webdriver-manager start'
				}
			}
		}
	});

	require('matchdep').filterDev('grunt-*').forEach(grunt.loadNpmTasks);		
	
	grunt.registerTask('default', 'connect:dist');
	grunt.registerTask('serve', function (target) {	

		if (target === 'development') {    
			return grunt.task.run(['ngconstant:development', 'connect:dist', 'connect:mock', 'watch:protractor']);
		}		
		if (target === 'unit_tests') {    
			return grunt.task.run(['ngconstant:development', 'connect:dist', 'connect:mock', 'protractor_webdriver', 'protractor:run', 'watch:protractor']);
		}
		if (target === 'integration_tests') {    
			return grunt.task.run(['ngconstant:integration','connect:int', 'protractor_webdriver', 'protractor:run', 'watch:protractor']);
		}
		if (target === 'integration') {    
			return grunt.task.run(['ngconstant:integration','connect:int', 'watch:protractor']);
		}
		if (target === 'qualification') {    
			return grunt.task.run(['ngconstant:qualification','connect:qualif', 'watch:protractor']);
		}  
	});
}; 
