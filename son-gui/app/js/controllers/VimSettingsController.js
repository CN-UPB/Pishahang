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

SonataApp.controller('VimSettingsController',['$rootScope','$scope','$routeParams','$location','$http',function($rootScope,$scope, $routeParams, $location, $http){
	
(function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
	$scope.new_vim = {};
  $scope.new_vim.compute_configuration={};
  $scope.new_vim.networking_configuration={};
  $scope.new_wim = {};
  $scope.getVimsTries = 0;
  $scope.getWimsTries = 0;


$scope.getVimDetails = function(vim){
  $scope.selected_vim = vim;
  $("#vim_details").openModal();
}

$scope.getWimDetails = function(wim){
  $scope.selected_wim = wim;
  $('#wim_details').openModal();  
}



	$scope.post_a_vim = function(){
		$http({
          method  : 'POST',
          url     : $scope.apis.vims,
          headers : { 'Content-Type': 'application/json','Accept':'application/json' },
          data    : $scope.new_vim
         })
          .success(function(data) {
            $scope.regetVims();  	        
	        $('#new_vim_installed').openModal();  
        });	
  }


  $scope.post_a_wim = function(){
    $http({
          method  : 'POST',
          url     : $scope.apis.wims,
          headers : { 'Content-Type': 'application/json','Accept':'application/json' },
          data    : $scope.new_wim
         })
          .success(function(data) {
          
          console.log(data);
          $('#new_wim_installed').openModal();
            $scope.regetWims();  
          
        });
  }

	

  $scope.regetVims = function(){
    $scope.loading =1;
      
      $http({
          method  : 'GET',
          url     : $scope.apis.vims,
          headers : { 'Content-Type': 'application/json','Accept':'application/json' }
         }).success(function(data) {
            var uuid = data.items.request_uuid;
            setTimeout(function(){

              $http({
              method  : 'GET',
              url     : $scope.apis.vims+'/'+uuid,
              headers : { 'Content-Type': 'application/json','Accept':'application/json'}
             })
              .error(function (data, status, headers, config) {
                  $scope.zero_vims = 1;
                  $scope.loading=0;

                  if($scope.getVimsTries<5){
                    
                    $scope.getVimsTries++;
                    $scope.regetVims();

                  }

                  //EDO
              })
              .success(function(datamm) {
                $scope.vims = new Array();
                $scope.vims=datamm;
                

                if($scope.vims.length==0){
                  $scope.zero_vims = 1;
                  $scope.loading=0;
                }else{
                  $scope.vims.forEach(function(vim,index){
                    $scope.setVimStatus(vim);
                    $scope.zero_vims=0;
                    $scope.loading=0;
                  });  
                }

              });   


            }, 2500);


          });

  }

	$scope.getVims = function(){
      $scope.zero_vims = 0;
      $scope.loading =1;
      	$http({
          method  : 'GET',
          url     : $scope.apis.vims,
          headers : { 'Content-Type': 'application/json','Accept':'application/json' }
         }).success(function(data) {
            
            var uuid = data.items.request_uuid;
            setTimeout(function(){

              $http({
              method  : 'GET',
              url     : $scope.apis.vims+'/'+uuid,
              headers : { 'Content-Type': 'application/json','Accept':'application/json'}
             })
              .error(function (data, status, headers, config) {
                  $scope.zero_vims = 1;
                  $scope.loading=0;
                  
                  if($scope.getVimsTries<5){
                    
                    $scope.getVimsTries++;
                    $scope.regetVims();

                  }
              })
              .success(function(datamm) {
                
                $scope.vims = new Array();
                $scope.vims=datamm;

                if($scope.vims.length==0){
                  $scope.zero_vims = 1;
                  $scope.loading=0;

                  if($scope.getVimsTries<5){
                    $scope.getVimsTries++;
                    $scope.regetVims();
                  }

                }else{
                  $scope.vims.forEach(function(vim,index){
                    $scope.setVimStatus(vim);
                    $scope.zero_vims=0;
                    $scope.loading=0;
                  });  
                }
                

              });   

            },2500);



          });


	}


  $scope.regetWims = function(){
    
      $scope.zero_wims = 0;
      $scope.loading_wims =1;

    $http({
          method  : 'GET',
          url     : $scope.apis.wims,
          headers : { 'Content-Type': 'application/json','Accept':'application/json' }
         }).success(function(data) {
            var uuid = data.items.request_uuid;
            setTimeout(function(){

              $http({
              method  : 'GET',
              url     : $scope.apis.wims+'/'+uuid,
              headers : { 'Content-Type': 'application/json','Accept':'application/json'}
             }).error(function (data, status, headers, config) {
                  $scope.zero_wims = 1;
                  $scope.loading_wims=0;

                  if($scope.getWimsTries<5){                    
                    
                    $scope.getWimsTries++;
                    $scope.regetWims();                    
                  }
              })
              .success(function(datamm) {
                
                $scope.wims = new Array();
                $scope.select = {};
                $scope.select.wims = new Array();
                
                $scope.m=datamm;

                 if($scope.m.length==0){
                  $scope.zero_wims = 1;
                  $scope.loading_wims=0;
                }else{
                  $scope.m.forEach(function(wim,index){
                    
                    var x = {};
                    x.uuid = wim.uuid;
                    x.name = wim.name;
                    x.attached_vims = wim.attached_vims;
                    x.status = "-";
                    $scope.wims.push(x);
                    $scope.select.wims.push(x);

                  });  

                  $scope.zero_wims=0;
                    $scope.loading_wims=0;
                }

              });   


            }, 2500);


          });
  }

  $scope.getWims = function(){

        $http({
          method  : 'GET',
          url     : $scope.apis.wims,
          headers : { 'Content-Type': 'application/json','Accept':'application/json' }
         }).success(function(data) {
            var uuid = data.items.request_uuid;
            

              $http({
              method  : 'GET',
              url     : $scope.apis.wims+'/'+uuid,
              headers : { 'Content-Type': 'application/json','Accept':'application/json'}
             }).error(function (data, status, headers, config) {
                  $scope.zero_wims = 1;
                  $scope.loading_wims=0;

                  if($scope.getWimsTries<5){                    
                    $scope.getWimsTries++;
                    $scope.regetWims();
                  }
              })
              .success(function(datamm) {
                
                $scope.wims = new Array();                
                $scope.m=(datamm?datamm:[]);
                
                if($scope.getWimsTries<5 && datamm.length==0){                    
                    $scope.getWimsTries++;
                    $scope.regetWims();
                    
                }else{
                  
                  if($scope.m.length>0){
                    
                    $scope.m.forEach(function(wim,index){
                  
                      var x = {};
                      x.uuid = wim.uuid;
                      x.name = wim.name;
                      x.attached_vims = wim.attached_vims;
                      x.status = "-";
                      $scope.wims.push(x);
                    }); 
                  }
                                   
                }               
                
                $('select').material_select();                

              });   

          });


  }



	$scope.setVimStatus = function(vim){
		vim.status = '-';
	}


    $scope.init = function(){
    	$scope.getVims();
      $scope.getWims();
    }

     
     $scope.$on("$destroy", function() {
         $scope.wims = [];
         $scope.vims = [];
    });
    
}]);
