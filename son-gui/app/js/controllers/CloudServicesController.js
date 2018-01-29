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

SonataApp.controller('CloudServicesController',['$rootScope','$http','$scope',function($rootScope,$http,$scope){
  (function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
  console.log('CLOUDSERVICES');
  $scope.openServiceInfo = function(cloudServices){
    $('#modal1').openModal();
    $scope.modal = {};
    $scope.modal.content = {};
    $scope.modal.content.title=cloudServices.csd.name;
    $scope.modal.content.cloudService = cloudServices;
  }


  $scope.getCloudServices = function(){
    console.info('Get Cloud Services call started. Url:'+$scope.apis.gatekeeper.cloud_services);
    $http({
      method  : 'GET',
      url     : $scope.apis.gatekeeper.cloud_services,
      headers : $rootScope.getGKHeaders()
    })
      .success(function(data) {
        console.info('Get Cloud Services From Url: '+$scope.apis.gatekeeper.cloud_services);
        $scope.cloudServices = data;
        console.log($scope.cloudServices);
      })
      .error(function(data){
        console.error('Get Cloud Services Failed. Get Url: '+$scope.apis.gatekeeper.cloud_services);
        console.error(data);
      })
  }





}]);
