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

 angular.module('NSR')
 .controller('NSRCtrl', ["$scope", "$rootScope", "NSRServices", "NSDServices", "ENV", "linkHeaderParser", "$localStorage", function($scope, $rootScope, NSRServices, NSDServices, ENV, linkHeaderParser, $localStorage) {

  $rootScope.username=$localStorage.currentUser.username;

  $scope.offset = 0;
  $scope.limit = 10;

  // retrieve NSD to server
  $scope.retrieveNSDs = (function() {
   NSRServices.retrieveNSDs(ENV)
   .then(function(result) {
     $rootScope.nSDs = result.data;
     $scope.generateNSDMap(result.data);

    }, function(error) {      
      if(JSON.stringify(error.data.code).indexOf('401') >= 0) {
        $rootScope.nSDs = '';
        $rootScope.nSRs = '';
      }
      $scope.error = angular.copy(JSON.stringify(error.data.message));
      $('#error.modal').modal('show');   
    })
 });
  
  $scope.retrieveNSDs();
  
  $scope.currentNSR = {};

  $scope.generateNSDMap = (function(obj){

   $rootScope.nSDsMap = new Object(); 	  
   $rootScope.activeNSDsMap = new Object(); 	  
   var uuid;
   var name;
   var vendor;
   var version;
   var status;

   for (var i=0; i<obj.length;i++){
    for (var key in obj[i]) {
      if (key == "uuid") uuid=obj[i][key];    
      if (key == "status") status=obj[i][key];
    }
    for (var key in obj[i]['nsd']) {		   
     if (key == "name") name=obj[i]['nsd'][key];		
     if (key == "vendor") vendor=obj[i]['nsd'][key];		
     if (key == "version") version=obj[i]['nsd'][key];		
   }	  	       
   $rootScope.nSDsMap[uuid] = name+"//"+vendor+"//"+version;
   if (status == "active") $rootScope.activeNSDsMap[name+vendor] = version+"//"+uuid;
 }

 $scope.retrieveNSRs($scope.offset);
});
  
   // retrieve NSR to server
   $scope.retrieveNSRs = (function(offset) {
     NSRServices.retrieveNSRs(ENV, offset)
     .then(function(result) {
       $rootScope.nSRs = result.data;

       if (JSON.stringify($rootScope.nSRs) == "[{}]"){
        $rootScope.nSRs = [];
       }

      //pagination
      var linkHeaderText = result.headers("Link");                    
      var link = linkHeaderParser.parse(linkHeaderText);                    
      $scope.totalPages = parseInt(link.last.offset)+1;
      $scope.limit = parseInt(link.last.limit);
      $scope.totalRecords = $scope.limit*$scope.totalPages;

    }, function(error) {
     if(JSON.stringify(error.data.code).indexOf('401') >= 0) {
      $rootScope.nSRs = '';
    }
    $scope.error = angular.copy(JSON.stringify(error.data.message));
    $('#error.modal').modal('show');   
  })
   });

  //$scope.retrieveNSRs();
  
  $scope.openDetailedNSR = function(data) {
   $scope.currentNSR = angular.copy(data);
   $('#detailedNSR.modal').modal('show');
   $($(".key.ng-binding.ng-scope")[0]).text("");//.text("NSR#" + $scope.currentNSR.uuid);      
 }

 $scope.openUpdateNSR = function(data) {
   $scope.currentNSR = angular.copy(data);
   $('#updateNSR.modal').modal('show');
 }

 $scope.openStopNSR = function(data) {
  $scope.currentNSR = angular.copy(data);
  $('#stopNSR.modal').modal('show');
 }


 $scope.updateNSR = function() {
   //console.log("$scope.currentNSD.uuid: "+$scope.currentNSD.uuid);
   NSRServices.updateNSR($scope.currentNSR.uuid,$scope.currentNSR.descriptor_reference,$scope.actualDescUuid, ENV)
   .then(function(result) {
     $('#updateNSR.modal').modal('hide');	 	 
     $('#updateRequest.modal').modal('show');    
   }, function(error) {		     
     $scope.error = angular.copy(JSON.stringify(error.data.message));
     $('#error.modal').modal('show');   
   })
 }

  $scope.stopNSR = function() {
   //console.log("$scope.currentNSD.uuid: "+$scope.currentNSD.uuid);
   NSRServices.stopNSR($scope.currentNSR.uuid, ENV)
   .then(function(result) {
     $('#stopNSR.modal').modal('hide');    
     $('#stopRequest.modal').modal('show');    
   }, function(error) {        
     $scope.error = angular.copy(JSON.stringify(error.data.message));
     $('#error.modal').modal('show');   
   })
 }

 $scope.getNSRDescriptorVersion = function(descriptorReference, nSDsMap ){

  //console.log("<<<<<<<<<<<<<<<<<<<< nSDsMap >>>>>>>>>>>>>>>>>>>>>>>>>>");
  //console.log(JSON.stringify(nSDsMap));
  //console.log("looking for "+descriptorReference+" reference");

   var nameVendorVersion = nSDsMap[descriptorReference];
   var descriptorVersion = nameVendorVersion.substring(nameVendorVersion.lastIndexOf("//")+2,nameVendorVersion.length);
   return descriptorVersion;
 }

 $scope.getActualNSDVersion = function(nSR, nSDsMap, activeNSDsMap){
	  
    var nameVendorVersion = nSDsMap[nSR.descriptor_reference];	  
    var nameVendor = nameVendorVersion.substring(0,nameVendorVersion.lastIndexOf("//"));
	  nameVendor = nameVendor.replace("//","");
	  var actualDescVersionUuid = activeNSDsMap[nameVendor];
	  
	  $scope.actualDescVersion = actualDescVersionUuid.substring(0,actualDescVersionUuid.lastIndexOf("//"));	  
	  $scope.actualDescUuid = actualDescVersionUuid.substring(actualDescVersionUuid.lastIndexOf("//")+2,actualDescVersionUuid.length);
	  
	  return $scope.actualDescVersion;
  }
  
  $scope.compareVersion = function (a, b) {
    if (a === b) {
     return 0;
   }

   var a_components = a.split(".");
   var b_components = b.split(".");

   var len = Math.min(a_components.length, b_components.length);

    // loop while the components are equal
    for (var i = 0; i < len; i++) {
        // A bigger than B
        if (parseInt(a_components[i]) > parseInt(b_components[i])) {
          return 1;
        }

        // B bigger than A
        if (parseInt(a_components[i]) < parseInt(b_components[i])) {
          return -1;
        }
      }

    // If one's a prefix of the other, the longer one is greater.
    if (a_components.length > b_components.length) {
      return 1;
    }

    if (a_components.length < b_components.length) {
      return -1;
    }

    // Otherwise they are the same.
    return 0;
  };

  $scope.emptyNSR = function() {
   $scope.currentNSR = {};
 };

 $scope.showPopover = function(nSR) {
   $scope.popoverIsVisible = true;
   $scope.hoveredNSR = nSR;
 };

 $scope.hidePopover = function() {
   $scope.popoverIsVisible = false;
 };

 $scope.clickPageButton=function(page){
   //console.log("button navigation clicked (page "+page+")");
   var offset = page-1;            
   $scope.retrieveNSRs(offset);
 }

}]);