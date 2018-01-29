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

SonataApp.controller('SignUpController',['$rootScope','$http','$scope',function($rootScope,$http,$scope){
		
		$rootScope.allowed =1;
    console.log('SignUpController');

        $scope.new_user = {};

          $scope.failedMessageVisibility = 0;
          
          
          $scope.backtoLogin = function(){
          	location.hash='/login';
          }

          $scope.submitSignUp = function(){
          	console.log($scope.new_user);

          	if($scope.password2!=$scope.new_user.password){
          		
          		$scope.error_message = "Please check the passwords fields. Passwords must be the same.";
	            $scope.error_message_view = 1;


          	}else{
          				$scope.success_message_view = 0;
	                $scope.error_message_view = 0;
          		    $scope.new_user.user_type = "developer";
          		$.ajax({
                  type: 'POST',
                  headers: {"Content-Type":"application/json"},
                  url: $rootScope.apis.gatekeeper.users,
                  data:JSON.stringify($scope.new_user),
                  async: false
	              })
	              .done(function(data, textStatus, jqXHR) {
	                  
	                  if(textStatus=='success'){
	                  	$scope.success_message = 'Your account has been created';
	                  	$scope.success_message_view = 1;
	                  	location.hash='/login/?s=1';

	                  }
	                  	
	                  console.log(textStatus);
	                  console.log(jqXHR);
	                  console.log(data);

	              })
	              .fail(function(jqXHR, textStatus, errorThrown) {
	                  /*$scope.failedMessageVisibility = 1;
	                  $rootScope.resp = 0;*/
	                  console.log(jqXHR);
                    console.log(textStatus);
                    console.log(errorThrown);

	                  /*console.log(jqXHR);*/
	                  	$scope.error_message = jqXHR.statusText+" "+jqXHR.responseJSON.error.message;
	                  	$scope.error_message_view = 1;
	                  
	              });

          	}
          	
          	 


            
          }

          $scope.httpGet = function(url,headers){
	
              $.ajax({
                  type: 'GET',
                  headers: headers,
                  url: url,
                  async: false
              })
              .done(function(data, textStatus, jqXHR) {
                  $rootScope.gitResp = data;
                  $rootScope.resp = 1;
                  location.hash = '/home';

              })
              .fail(function(jqXHR, textStatus, errorThrown) {
                  $scope.failedMessageVisibility = 1;
                  $rootScope.resp = 0;
              });
          }
           
}]);