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


(function (){
    'use sctict';

    angular
        .module('Login')
        .controller('LoginController', LoginController);
        
    function LoginController($rootScope, $location, $base64, AuthenticationService, ENV) {

        var vm = this;
        vm.login = login;
        vm.register = register;
        $rootScope.username = '';        
        logout();

        function login() {                        

            var data = { "username": vm.username , "password": vm.password };

            AuthenticationService.Login(data, ENV)
            .then(function(result) {
                $location.path('nSDs');
                $rootScope.username = vm.username;                                                    
                vm.currentUserSignedIn = true;
                //console.log("loginController - currentUserSignedIn: "+vm.currentUserSignedIn+", $rootScope.username: "+$rootScope.username);
            },function(error) {
                vm.error = true;                    
                vm.currentUserSignedIn = false;   
            })
        };       

        function logout() {                        
            
            var data = { "username": vm.username , "password": vm.password };

            AuthenticationService.Logout(data, ENV)
            .then(function(result) {
                // remove user from local storage and clear http auth header
                delete $localStorage.currentUser;
                delete $rootScope.username;  
                delete $rootScope.nSDs;
                delete $rootScope.nSRs;
                delete $rootScope.Requests;          
                $http.defaults.headers.common.Authorization = ''; 
            }, function(error) {
                vm.currentUserSignedIn = false;
            })                
        };

        function register() {
            
            var data = { "username": vm.user.username , "password": vm.user.password , "first_name": vm.user.firstName, "last_name": vm.user.lastName, "email": vm.user.userEmail, "phone_number": vm.user.phoneNumber, "user_type": "customer"};

            AuthenticationService.Register(data, ENV)
            .then(function(result) {                
                $('#success.modal').modal('show').on('hidden.bs.modal', function(e) {
                    $rootScope.$apply(function() {
                        $location.path('/login');                        
                    });                    
                });                                                
                
            }, function(error) {
                $rootScope.error = angular.copy(JSON.stringify(error.data.message));                                
                $('#error.modal').modal('show');     
            })             
        }      
    };    
})();