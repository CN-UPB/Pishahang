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

angular.module('NSD')
 .controller('InstNSDCtrl', ["$scope", "NSDServices", "ENV", "$localStorage", "$rootScope", function($scope, NSDServices, ENV, $localStorage, $rootScope) {

  $rootScope.username=$localStorage.currentUser.username;
  $scope.locations = [];  

  $scope.addNewIngress = function() {    
    $scope.ingresses.push({});
  };
    
  $scope.removeIngress = function() {
    if ($scope.ingresses.length > 1) {
      var lastItem = $scope.ingresses.length-1;
      $scope.ingresses.splice(lastItem);
    }    
  };
  
  $scope.addNewEgress = function() {    
    $scope.egresses.push({});
  };
    
  $scope.removeEgress = function() {
    if ($scope.egresses.length > 1) {
      var lastItem = $scope.egresses.length-1;
      $scope.egresses.splice(lastItem);
    }    
  };

  $scope.getLocations = function() {

    NSDServices.getVimRequests(ENV)
    .then(function(result) {         
      var response = result.data;      
      var vimRequest = JSON.stringify(response["items"]);
      var vims;      

      vimRequest = JSON.parse(vimRequest);

        vims='';
        var locationsAdded = false;

        (function loop (counter) {          
          setTimeout(function () {   

            NSDServices.getVims(ENV, vimRequest["request_uuid"])
            .then(function(result){
              if (result.data != ''){
                vims = result.data;

                if (vims.length!=0) {
                  //console.log("vims: "+JSON.stringify(vims));

                  for (var i in vims){
                    if ($scope.locations.indexOf(vims[i]["vim_city"]) === -1) {
                      $scope.locations.push(vims[i]["vim_city"]);
                      //console.log(vims[i]["vim_city"]+" added to locations");
                      locationsAdded = true;                      
                    }
                  }
                }
              }
            }, function(error) {
              $scope.error = angular.copy(JSON.stringify(err.data.message));
              $('#error.modal').modal('show'); 
            })
            
            if ((!locationsAdded)&&(--counter)) loop(counter);      //  decrement i and call my loop again if counter > 0
          }, 1000)
        })(10);
      
      callback($scope.locations);
    }, function(error) {
      $scope.error = angular.copy(JSON.stringify(error.data.message));
      $('#error.modal').modal('show');   
    })
  };

  $scope.getLocations();  

}]);