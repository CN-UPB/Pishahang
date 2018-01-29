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

SonataApp.controller('AllServicesController',['$rootScope','$http','$scope',function($rootScope,$http,$scope){
            (function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
           $scope.userServices = new Array();
           $scope.selected_services = new Array();
           $scope.remove_class_btn='disabled';
           

           $scope.deploy_service = function(id){
            console.info('A service with uuid:'+id+' is going to be instatiated');
            $http({
                method  : 'POST',
                url     : $scope.apis.gatekeeper.requests,
                headers : $rootScope.getGKHeaders(),
                data:{
                    'name':id
                  }
               })
                .success(function(data) {
                 console.log(data);
                 })
                .error(function(data){
                    console.error('Get Services Failed. Get Url: '+$scope.apis.gatekeeper.services);
                })
           }
           


           $scope.getServices = function(){
              $scope.getNetworkServices();
              $scope.getComplexServices();
           }

           $scope.getNetworkServices = function(){
             $http({
               method  : 'GET',
               url     : $scope.apis.gatekeeper.services,
               headers : $rootScope.getGKHeaders()
             })
               .success(function(data) {

                 console.info('Get Services From Url: '+$scope.apis.gatekeeper.services);

                 data.forEach(function (service, index) {
                   service.data = service.nsd;
                   service.type = 'Network Service';
                 });

                 data = data.filter(function(n){ return n.nsd; });

                 if (!$scope.services) {
                   $scope.services = data;
                 } else {
                   $scope.services.push.apply($scope.services, data);
                 }

                 $scope.services.forEach( function(service, index) {
                   service.checked = 0;
                 });

               })
               .error(function(data){
                 console.error('Get Services Failed. Get Url: '+$scope.apis.gatekeeper.services);
               })
           }

           $scope.getComplexServices = function(){
             $http({
               method  : 'GET',
               url     : $scope.apis.gatekeeper.complex_services,
               headers : $rootScope.getGKHeaders()
             })
               .success(function(data) {

                 console.info('Get Complex Services From Url: '+$scope.apis.gatekeeper.complex_services);

                 data.forEach(function (service, index) {
                   service.data = service.cosd;
                   service.type = 'Complex Service';
                 });

                 data = data.filter(function(n){ return n.cosd; });


                 if (!$scope.services) {
                   $scope.services = data;
                 } else {
                   $scope.services.push.apply($scope.services, data);
                 }

                 $scope.services.forEach( function(service, index) {
                   service.checked = 0;
                 });

               })
               .error(function(data){
                 console.error('Get Complex Services Failed. Get Url: '+$scope.apis.gatekeeper.services);
               })
           }

           $scope.openServiceInfo = function(service){
             $('#modal1').openModal();
             $scope.modal = {};
             $scope.modal.content = {};
             $scope.modal.content.title=service.name;

             $scope.modal.content.service = service;
           }

          $scope.openServiceGraphs = function(service){
             $('#modal1').openModal();
             $scope.modal = {};
             $scope.modal.content = {};
             $scope.modal.content.title=service.name;
             $scope.modal.content.service = service;
             
          }
          $scope.closeModal = function(){
             $('#modal1').closeModal(); 
          }
        

          $scope.remakeChecked = function(service){

            $scope.selected_services = new Array();
            $scope.services.forEach( function(service, index) {
              if(service.checked){
                $scope.selected_services.push(service);
              }
            });
              if($scope.selected_services.length>0)
                $scope.remove_class_btn = 'enabled';
              else
                $scope.remove_class_btn = 'disabled';
          }


           
}]);
