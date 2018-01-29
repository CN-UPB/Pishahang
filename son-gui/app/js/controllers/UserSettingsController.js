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

SonataApp.controller('UserSettingsController', function($scope, $routeParams, $location, $http,$rootScope,$filter) {

		$scope.change_password_request = false;
		$scope.single_user = true;
		$scope.password_field_popup = false;
		$scope.delete_user_popup_view = false;

		$scope.changePass = function(){
			$scope.change_password_request = true;
		}
		$scope.cancel_pressed = function(){
			$scope.pop_one_view = 0;
		}
		$scope.pop_up_close = function(){
			$scope.pop_up_view = 0;
		}
		$scope.logged_again_ok = function(){
			
			$http({
                method  : 'PUT',
                url: $scope.apis.gatekeeper.users+'?username='+$rootScope.username,
                headers : $rootScope.getGKHeaders(),
                data:{
                	'username'	:$rootScope.username,
                	'password'	:$scope.thisuser.password_one,
                	'email'		:$scope.thisuser.email,
                	'user_type'	:$scope.thisuser.user_type,
                	'last_name'	:$scope.thisuser.last_name,
                	'first_name':$scope.thisuser.first_name
                }
              })
	       .success(function(datas) {
	       		$rootScope.logout();	        	

	        });
			
		}
		$scope.openModalForPassword = function(){
			$scope.password_field_popup = true;
		}
		$scope.cancel_password_field_pressed = function(){
			$scope.password_field_popup = false;
		}

		$scope.delete_user = function(user){
			console.log(user);
			$scope.selected_for_delete_user = user;
			$scope.delete_user_popup_view = true;
		}
		$scope.delete_user_confirmed = function(){
			$http({
                method  : 'DELETE',
                url: $scope.apis.gatekeeper.users+'?username='+$scope.selected_for_delete_user.username,
                headers : $rootScope.getGKHeaders(),
                
              })
	       .then(function(datas) {
	       		$scope.success_message_view = 1;
				$scope.success_message_text = "The user has been deleted";

	        },function(e){
	        	$scope.error_message_view = 1;
				$scope.error_message_text = e.data.error.message;
	        });
		}
		$scope.update_credentials = function(){
			$scope.password_field_popup = false;
			var data = {
			                	'username'	:$rootScope.username,
			                	'email' 	:$scope.thisuser.email,
			                	'user_type'	:$scope.thisuser.user_type,
			                	'last_name'	:$scope.thisuser.last_name,
			                	'first_name':$scope.thisuser.first_name,
			                	'password'	:$scope.thisuser.password_ma
			                }
						$http({
			                method  : 'PUT',
			                url: $scope.apis.gatekeeper.users+'?username='+$rootScope.username,
			                headers : $rootScope.getGKHeaders(),
			                data:data
			              })
				       .then(function(datas) {
				       		$scope.success_message_view = 1;
				       		$scope.success_message_text = "The user profile has been updated correctly";
				       		$scope.pop_up_view = 1;
				       		$scope.pop_up_h3 = 'User Profile Updated';
				       		$scope.pop_up_p = 'The user profile has been updated correctly';
				        },function(e){
				        	$scope.error_message_view = 1;
							$scope.error_message_text = e.data.error.message;
							console.log(e);
				        });
		}
		$scope.saveUserInfo = function(){

			$scope.error_message_view = 0;
			$scope.pop_one_view = 0;

			if($scope.thisuser.password_one != $scope.thisuser.password_two){
				$scope.error_message_view = 1;
				$scope.error_message_text = "Password fields are not equal. Please check the password you will set";
			}else{

				if($scope.thisuser.password_one!='' && $scope.thisuser.password_one!='undefined' && $scope.thisuser.password_one!=undefined){
					$scope.pop_one_view = 1;
				
				}else{
					
					$scope.openModalForPassword();
				}

			}
		}
     	
     	$scope.getUserInfo = function(){
				
	     	$http({
                method  : 'GET',
                url: $scope.apis.gatekeeper.users,
                headers : $rootScope.getGKHeaders()
              })
	       .success(function(datas) {
	       		
	       		if(datas.length>0){
	       			$scope.single_user = false;
	       			$scope.users = datas;

	       			$scope.users.forEach(function(user,index){
	       				if(user.username==$rootScope.username){
	       					$scope.thisuser = user;
	       					$scope.thisuser.password_ma = "";
	       				}
	       					
	       			})
	       		}else{
	       			$scope.thisuser = datas;	
	       		}
	       		
	        })

   		}
   		$scope.getUserInfo();

     (function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
	 
	 	$scope.$on('$viewContentLoaded', function(event) {
	  	
	    	$('select').material_select();
	  
	    });


    });


