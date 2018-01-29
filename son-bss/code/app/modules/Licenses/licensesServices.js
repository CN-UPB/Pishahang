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

angular.module('Licenses')
    .factory('LicensesServices',["$http","$q","$localStorage",function ($http,$q,$localStorage) {
        return {            
            retrieveNSDs:function(ENV,offset){

                var defer=$q.defer();   
                var maxSafeInteger = Math.pow(2,16) - 1;            
                //$http.get(ENV.apiEndpoint+"/licenses?username="+username+"&limit="+maxSafeInteger+"&offset=0")            
                $http.get(ENV.apiEndpoint+"/services?status=active&limit="+maxSafeInteger+"&offset="+offset)
                .then(function successCallback(result){
                    defer.resolve(result)})
                .catch(function errorCallback(error){
                    defer.reject(error)});
                return defer.promise;
            },
            requestLicense:function(ENV, service_id, licence_url){                
                var defer=$q.defer();
                var data={"service_uuid":service_id, "licence_type": "PRIVATE", "licence_url":licence_url};
                $http.post(ENV.apiEndpoint+"/licences",data)
                .then(function successCallback(result){
                    defer.resolve(result)})
                .catch(function errorCallback(error){
                    defer.reject(error)});
            
                return defer.promise;
            }
        }
    }]);