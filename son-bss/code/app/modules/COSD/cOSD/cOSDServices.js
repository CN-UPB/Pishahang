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

 angular.module('COSD')
 .factory('COSDServices',["$http","$q","$localStorage", function ($http,$q,$localStorage) {
    return {
        retrieveCOSDs:function(ENV, offset){

            var defer=$q.defer();		        
            $http.get(ENV.apiEndpoint+"/complex-services?status=active&limit="+10+"&offset="+offset)
            .then(function successCallback(result){
                defer.resolve(result)})
            .catch(function errorCallback(error){
                defer.reject(error)});
            return defer.promise;
        },
        
        instantiateCOSD:function(id, ingresses, egresses, ENV){
            var defer=$q.defer();

            /* check for empty ingress/egress */

            if (Object.keys(ingresses).length > 0) {
                var element = ingresses.pop();
                if ( angular.toJson(element) != "{}") {
                    ingresses.push(element);
                }
            }

            if (Object.keys(egresses).length > 0) {
                var element = egresses.pop();
                if ( angular.toJson(element) != "{}") {
                    egresses.push(element);
                }
            }

            var data={"service_uuid":id, "ingresses": ingresses, "egresses":egresses};
            $http.post(ENV.apiEndpoint+"/requests",data)
            .then(function successCallback(result){defer.resolve(result)})
            .catch(function errorCallback(error){defer.reject(error)});
            
            return defer.promise;
        },

        requestLicense:function(ENV, id, licence_url){                
            var defer=$q.defer();
            var data={"service_uuid":id, "licence_type": "PRIVATE", "licence_url":licence_url};
            $http.post(ENV.apiEndpoint+"/licences",data)
            .then(function successCallback(result){defer.resolve(result)})
            .catch(function errorCallback(error){defer.reject(error)});
            
            return defer.promise;
        },

        getVimRequests:function(ENV){
            var defer=$q.defer();            
            $http.get(ENV.apiEndpoint+"/vims")
            .then(function successCallback(result){
                //console.log("getVimRequests result: "+JSON.stringify(result));
                defer.resolve(result);
            })
            .catch(function errorCallback(error){defer.reject(error)});

            return defer.promise;
        },

        getVims:function(ENV, vimRequest){
            
            var defer=$q.defer();
            var data;

            $http.get(ENV.apiEndpoint+"/vims/"+vimRequest)
            .then(function successCallback(result){                
                defer.resolve(result);
            })
            .catch(function errorCallback(error){
                defer.reject(error)
            });

            return defer.promise;
        }
    }
}]);
