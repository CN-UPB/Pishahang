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

angular.module("COSD",["config"]);
    
angular.module("NSD",["config"]);
    
angular.module("Requests",["config"]);

angular.module("NSR",["config"]);

angular.module("COSR",["config"]);

angular.module("Login",["config"]);  

angular.module("Register",["config"]);  

angular.module("Logout",["config"]);

angular.module("Licenses",["config"]);   

angular.module("SonataBSS", ["angular-json-tree", "ui.router", "formly", "formlyBootstrap", "ngAnimate", "ig.linkHeaderParser"

    ,"ngStorage", "bw.paging", "base64", "ui.bootstrap"

    ,"COSD"

    ,"NSD"

    ,"Requests"
	
	  ,"NSR"

    ,"COSR"
	
	  ,"Login"

    ,"Register"

    ,"Logout"

    ,"Licenses"

    ])    
    .config(["$stateProvider", "$urlRouterProvider", "$locationProvider", "$qProvider", function ($stateProvider, $urlRouterProvider, $locationProvider, $qProvider) {
        
        $stateProvider
            .state("COSD",{
              url: "/cOSDs",
              templateUrl: "modules/COSD/cOSD/views/cOSDs.html",
              controller: "COSDCtrl"
            })
            .state("NSD",{
                url: "/nSDs",
                templateUrl: "modules/NSD/nSD/views/nSDs.html",
                controller: "NSDCtrl"
             })
            .state("Requests",{
                url: "/requests",
                templateUrl: "modules/Requests/Requests/views/requests.html",
                controller: "RequestsCtrl"
            })
            .state("NSR",{
                url: "/nSRs",
                templateUrl: "modules/NSR/nSR/views/nSRs.html",
                controller: "NSRCtrl"
            })
            .state("COSR",{
              url: "/cOSRs",
              templateUrl: "modules/COSR/cOSR/views/cOSRs.html",
              controller: "COSRCtrl"
            })
            .state("Login",{
                url: "/login",
                templateUrl:"login/login.html",
                controller: "LoginController",
                controllerAs: "vm"
            })   
            .state("Logout",{
                url: "/login",
                templateUrl:"login/login.html",
                controller: "LoginController"
            })
            .state("Register",{
                url: "/register",
                templateUrl:"login/register.html",
                controller: "LoginController",
                controllerAs: "vm"
            })
            .state("Licenses",{
                url: "/licenses",
                templateUrl:"modules/Licenses/views/licensesIndex.html",
                controller: "LicensesTabsCtrl"
            })

        $urlRouterProvider.otherwise("/login");
        $locationProvider.hashPrefix('');
        $qProvider.errorOnUnhandledRejections(false);
    }])    
    .run(["$rootScope", "$http", "$location", "$localStorage", function ($rootScope, $http, $location, $localStorage) {                
        //console.log("=====================================================");
        // keep user logged in after page refresh
        if ($localStorage.currentUser) {            
            $http.defaults.headers.common.Authorization = 'Bearer ' + $localStorage.currentUser.token;
        }
        
        // redirect to login page if not logged in and trying to access a restricted page
        $rootScope.$on('$locationChangeStart', function (event, next, current) {
            var publicPages = ['/login', '/register'];
            var restrictedPage = publicPages.indexOf($location.path()) === -1;
            if (restrictedPage && !$localStorage.currentUser) {
                console.log('restricted page and not currentuser: changing to login page');
                $location.path('/login');
            }
        });
    }]);
