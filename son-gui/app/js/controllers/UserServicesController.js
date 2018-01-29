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

SonataApp.controller('UserServicesController',['$rootScope','$http','$scope',function($rootScope,$http,$scope){
(function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
           $scope.userServices = new Array();
           $scope.selected_services = new Array();
           $scope.remove_class_btn='disabled';
           

           $scope.userServices.push({
           	'id':1,
            'checked':false,
           	'name':'Service One',
           	'version':'Service version',
           	'description':'Service Description',
           	'status':'Service Status',
           });
           $scope.userServices.push({
           	'id':2,
            'checked':false,
           	'name':'Service Two',
           	'version':'Service version Two',
           	'description':'Service Description Two',
           	'status':'Service Status Two',
           });
           $scope.userServices.push({
           	'id':3,
            'checked':false,
           	'name':'Service Three',
           	'version':'Service version Three',
           	'description':'Service Description Three',
           	'status':'Service Status Three',
           });


          $scope.openServiceGraphs = function(service){
             $('#modal1').openModal();
             console.log(service);
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
            $scope.userServices.forEach( function(service, index) {
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