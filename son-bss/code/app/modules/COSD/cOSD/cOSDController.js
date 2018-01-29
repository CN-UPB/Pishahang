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
 .controller('COSDCtrl', ["$scope", "$rootScope", "COSDServices", "ENV", "linkHeaderParser", "$localStorage", function($scope, $rootScope, COSDServices, ENV, linkHeaderParser, $localStorage) {

  $rootScope.username=$localStorage.currentUser.username;

  $scope.currentCOSD = {};
  $scope.offset = 0;
  $scope.limit = 10;
  $scope.ingresses = [{}];
  $scope.egresses = [{}];

  // retrieve COSD to server
  $scope.retrieveCOSDs = (function(offset) {

    COSDServices.retrieveCOSDs(ENV, offset)
      .then(function(result) {

       var cOSDs = result.data;
       var licenses = $rootScope.userLicenses;       

       if (JSON.stringify(cOSDs) == "[{}]") {
         cOSDs = [];
       }
      $rootScope.cOSDs = cOSDs;

      //pagination
      var linkHeaderText = result.headers("Link");                    
      var link = linkHeaderParser.parse(linkHeaderText);                    
      $scope.totalPages = parseInt(link.last.offset)+1;
      $scope.limit = parseInt(link.last.limit);
      $scope.totalRecords = $scope.limit*$scope.totalPages;

      }, function(error) {      
        if(JSON.stringify(error.data.code).indexOf('401') >= 0) {
          $rootScope.cOSDs = '';
          $rootScope.userLicenses = '';
        }
        $scope.error = angular.copy(JSON.stringify(error.data.message));
        $('#error.modal').modal('show');   
      })
    });    

  $scope.retrieveCOSDs($scope.offset);

  $scope.openAddCOSD = function() {
   $scope.currentCOSD = {};
   $('#addCOSD.modal').modal('show');
 }

  // save COSD to server
  $scope.saveCOSD = function() {
   COSDServices.saveCOSD($scope.currentCOSD)
   .then(function(result) {
     $rootScope.cOSDs.push(result.data);
   }, function(error) {
     $scope.error = angular.copy(JSON.stringify(error.data.message));
     $('#error.modal').modal('show');   
   })
 }

 $scope.openUpdateCOSD = function(data) {
   $scope.currentCOSD = angular.copy(data);
   $('#updateCOSD.modal').modal('show');
   $($(".key.ng-binding.ng-scope")[0]).text("COSD#" + $scope.currentCOSD.uuid);
 }

 $scope.openInstantiateCOSD = function(data) {
   $scope.currentCOSD = angular.copy(data);
   $('#instantiateCOSD.modal').modal('show');
 }


 $scope.instantiateCOSD = function() {
   COSDServices.instantiateCOSD($scope.currentCOSD.uuid, $scope.ingresses, $scope.egresses, ENV)
   .then(function(result) {
     $('#instantiateCOSD.modal').modal('hide');
     $scope.instantiateRequest = result.data;
     $('#instantiateRequest.modal').modal('show');    
   }, function(error) {
     $scope.error = angular.copy(JSON.stringify(error.data.message));
     $('#error.modal').modal('show');   
   })

   $scope.cleanInstantiationIngressEgress();

 }

 $scope.emptyCOSD = function() {
   $scope.currentCOSD = {};
   $scope.cleanInstantiationIngressEgress();
 };
 
 $scope.showPopover = function(cOSD) {
   $scope.popoverIsVisible = true;
   $scope.hoveredCOSD = cOSD;
 };

 $scope.hidePopover = function() {
   $scope.popoverIsVisible = false;
 };

 $scope.clickPageButton=function(page){
   //console.log("button navigation clicked (page "+page+")");
   var offset = page-1;            
   $scope.retrieveCOSDs(offset);
 }

 $scope.showModalRequestingLicense = function(service_id, licence_url) {
   $scope.service_id = angular.copy(service_id);
   $scope.licence_url = angular.copy(licence_url);
   console.log("service_id: "+$scope.service_id+" and licence_url: "+$scope.licence_url);
   $('#getLicense.modal').modal('show');
 }


 $scope.requestLicense = function(service_id, licence_url) {
   COSDServices.requestLicense(ENV, service_id, licence_url)
   .then(function(result) {
     $('#getLicense.modal').modal('hide');   
     $scope.licenseRequest = result.data;
     $('#getLicenseResponse.modal').modal('show');    
   }, function(error) {
     $scope.error = angular.copy(JSON.stringify(error.data.message));
     $('#error.modal').modal('show');   
   })
 }

 $scope.cleanInstantiationIngressEgress = function() {
   $scope.ingresses = [{}];
   $scope.egresses = [{}];
 }

}]);
