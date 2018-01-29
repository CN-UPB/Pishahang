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


angular.module('Login')
.factory('AuthenticationService', ["$http", "$localStorage", "$q",function ($http,$localStorage,$q) {
    return {
        Login:function(data, ENV, callback) {

            var defer=$q.defer();
            
            if (ENV.userManagementEnabled == 'false') {                
            
                var fakeToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6InNvbmF0YSIsImFkbWluIjp0cnVlfQ.AdgPchW4kBolbrVPn8YlrNIOx8XqcHcO_bCR2gclGyo';

                $localStorage.currentUser = { username: 'sonata', token: fakeToken , user_role:'customer'};
                $http.defaults.headers.common.Authorization = 'Bearer ' + fakeToken;
                defer.resolve(true);
            } else {
                
                $http.post(ENV.apiEndpoint+'/sessions', data)
                .then(function successCallback(response){

                    // login successful if there's a token in the response                
                    if (response.data.token) {
                    
                        // store username and token in local storage to keep user logged in between page refreshes                    
                        $localStorage.currentUser = { username: data.username, token: response.data.token.access_token, user_role: response.data.user_role };
                    
                        // add jwt token to auth header for all requests made by the $http service
                        //$http.defaults.headers.common.Authorization = 'Bearer ' + response.token;
                        $http.defaults.headers.common.Authorization = 'Bearer ' + response.data.token.access_token;

                        // execute callback with true to indicate successful login                    
                        defer.resolve(response);
                    } else {
                        // execute callback with false to indicate failed login
                        error='{"code": "401", "message":"Response does not contain token"}';                    
                        defer.reject(error);
                    }
                })
                .catch(function errorCallback(error){
                    defer.reject(error)
                });                
            }

            return defer.promise;            
        },

        Logout:function(data, ENV, callback) {              

            var defer=$q.defer();

            if (ENV.userManagementEnabled == 'false') {                                               
                defer.resolve(true);
            } else {                
                $http.delete(ENV.apiEndpoint+'/sessions', data)
                .then(function successCallback(response){
                    defer.resolve(response);
                })                    
                .catch(function errorCallback(error){
                    defer.reject(error)
                });            
            }

            return defer.promise;            
        },

        Register:function(data, ENV, callback) {
        
            var defer=$q.defer();

            if (ENV.userManagementEnabled == 'false') {
                defer.resolve(true);
            } else {
                $http.post(ENV.apiEndpoint+'/users', data)
                .then(function successCallback(response){                                    
                    defer.resolve(response)                    
                })
                .catch(function errorCallback(error){                                        
                    defer.reject(error)                  
                });
            }            
            return defer.promise;
        }
    }
}]);