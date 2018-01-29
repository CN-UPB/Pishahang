/*
Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
ALL RIGHTS RESERVED.
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote 
products derived from this software without specific prior written 
permission.
This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through 
the Horizon 2020 and 5G-PPP programmes. The authors would like to 
acknowledge the contributions of their colleagues of the SONATA 
partner consortium (www.sonata-nfv.eu).
*/

SonataApp.controller('MainController',['$rootScope','$scope','$routeParams', '$location', '$http',function($rootScope,$scope, $routeParams, $location, $http) {
   $scope.debug=(window.location.origin=="http://localhost"?true:false);


    $scope.todos = new Array();
    (function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);

    $rootScope.setStorage = function(valuename,valuevalue){
      window.localStorage.setItem(valuename,valuevalue);
    }

    $rootScope.getStorage = function(valuename){
      return window.localStorage.getItem(valuename);
    }

    $rootScope.getToken = function(){

        return $rootScope.getStorage('sonata-token');

    }

    $rootScope.getUserName = function(){
      return $rootScope.getStorage('sonata-username');
    }
    $rootScope.username=$rootScope.getUserName();


    $rootScope.checkIfValid = function(token){

      return true;

    }

    $rootScope.checkIfNull = function(val){
      return angular.isUndefined(val) || val === null
    }

   $rootScope.getIndexOf=function(arr, val, prop) {
      var l = arr.length,
        k = 0;
      for (k = 0; k < l; k = k + 1) {
        if (arr[k][prop] === val) {
          return k;
        }
      }
      return -1;
    }

     $scope.getServices = function(){

                if($scope.debug==false){
                  var protocol  = window.location.protocol;
                  var host      = window.location.hostname;

                  var gk_url = protocol+'//'+host+'/api/v2';
                  var mon_url = protocol+'//'+host+'/monitoring';
                  var vims_url = protocol+'//'+host+'/api/v2';
                  var logs_url = protocol+'//'+host+'/logs';

                }else{
                  var gk_url = 'https://sp.int3.sonata-nfv.eu/api/v2';
                  var mon_url = 'http://sp.int3.sonata-nfv.eu:8000';
                  var vims_url = 'http://sp.int3.sonata-nfv.eu:32001/api/v2';
                  var logs_url = 'http://logs.sonata-nfv.eu:12900/logs';
                }
                  console.log("protocol: "+protocol);
                  console.log("host: "+host);

                  $scope.configuration = {
                    'logs_range':'86400' //time range (minutes before)
                  }

                  $scope.apis = {
                        'monitoring_css':mon_url+'/api/v1/cloud-services',
                        'monitoring':mon_url+'/api/v1/prometheus/metrics/data',
                        'monitoring_list':mon_url+'/api/v1/prometheus/metrics/list',
                        'logs':logs_url+'/search/universal/relative?',
                        'vims':vims_url+'/vims',
                        'wims':vims_url+'/wims',
                        'monitoring_data':gk_url+'/kpis/collected',
                        'gatekeeper':{
                          'services' :gk_url+'/services',
                          'complex_services':gk_url+'/complex-services',
                          'packages' :gk_url+'/packages',
                          'functions':gk_url+'/functions',
                          'cloud_services': gk_url+'/cloud-services',
                          'requests' :gk_url+'/requests',
                          'kpis'     :gk_url+'/kpis',
                          'users'    :gk_url+'/users',
                          'user_sessions':gk_url+'/sessions',
                        }
                      };

              $rootScope.apis = $scope.apis;
              $rootScope.gk_headers = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer '+$rootScope.getStorage('sonata-token')
              };
                     $rootScope.checkTokenValidity();
           }

    $rootScope.getGKHeaders = function(){
      var header = {};
      header = {'Content-Type': 'application/json',
                    'Authorization': 'Bearer '+$rootScope.getStorage('sonata-token')};
                    return header;
    }

    $rootScope.logout = function(){
      $rootScope.is_user_logged_in = false;
      $rootScope.gk_headers = {};
      $rootScope.token = '';
      delete window.localStorage['sonata-token'];
      delete window.localStorage['sonata-username'];

      location.hash='/login';

    }


$rootScope.checkTokenValidity = function(){     

          $http({
              method  : 'GET',
                url: $scope.apis.gatekeeper.users,
                headers : $rootScope.getGKHeaders()
          }).then(function successCallback(response) {
            console.log("TOKEN is Valid");
          }, function errorCallback(response) {
            console.log("The token is not valid");
            console.log(response);
            $rootScope.logout();
          });
      }


    $scope.checkAuthorization = function(){

      if($rootScope.is_user_logged_in==false){
        $rootScope.logout();
      }
      if($location.url()!='/signup' && $location.url()!='/login'){

            var localStorageToken = $rootScope.getStorage('sonata-token');

            if($rootScope.checkIfNull(localStorageToken)){

              $rootScope.is_user_logged_in = false;
              delete window.localStorage['sonata-token'];
              location.hash='/login';
            }
            else{
              if($rootScope.checkIfValid(localStorageToken)){
                $rootScope.is_user_logged_in = true;
              }
            }
      }
    }
    $scope.checkAuthorization();

    $scope.checkTokenValidity = function(){


          $http({
              method  : 'GET',
                url: $scope.apis.gatekeeper.users,
                headers : $rootScope.getGKHeaders()
          }).then(function successCallback(response) {
            console.log("TOKEN is Valid");
          }, function errorCallback(response) {
            console.log("The token is not valid");
            console.log(response);
            $rootScope.logout();
      });
    }

$scope.alerts_visibility = 0;


$rootScope.FixTimestamp = function(timestamp){

    timestamp = timestamp.toString();
    timestamp = timestamp.replace('.','');

    if(timestamp.length==12)
        timestamp=timestamp+'0';
    else if(timestamp.length==11)
      timestamp = timestamp+'00';
    else if(timestamp.length==10)
      timestamp = timestamp+'000';
    else if(timestamp.length==9)
      timestamp = timestamp+'0000';

    timestamp = parseInt(timestamp);
    return timestamp;
}


    $scope.changeHash = function(newHash){
      location.hash = newHash;
    }

  $rootScope.checkIfFilesAreThere = function(){

    return 1;
  }


    }]);
