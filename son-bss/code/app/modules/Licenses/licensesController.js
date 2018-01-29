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

angular.module('Licenses')
    .controller('LicensesCtrl', ["$scope", "$rootScope", "$localStorage", "LicensesServices", "ENV", "linkHeaderParser", function ($scope, $rootScope, $localStorage, LicensesServices, ENV, linkHeaderParser) {

        $rootScope.username=$localStorage.currentUser.username;
        $scope.offset = 0;
        $scope.limit = 10;
        $scope.user_name = $localStorage.currentUser.username;
        $scope.nSDs = {};

        $scope.retrieveNSDs = (function (offset) {
            LicensesServices.retrieveNSDs(ENV, offset)
            .then(function (result) {                
                $scope.nSDs = result.data;

                if ($localStorage.currentUser.user_role === "developer"){
                    $rootScope.licence_use = "Package Creation";
                } else {
                    //customer
                    $rootScope.licence_use = "Instantiation";
                }

                if (JSON.stringify($scope.nSDs) == "[{}]"){
                    $scope.nSDs = [];
                }

                //pagination
                var linkHeaderText = result.headers("Link");                    
                var link = linkHeaderParser.parse(linkHeaderText);                    
                $scope.totalPages = parseInt(link.last.offset)+1;
                $scope.limit = parseInt(link.last.limit);
                $scope.totalRecords = $scope.limit*$scope.totalPages;                

            }, function (error) {
                if (JSON.stringify(error.data.code).indexOf('401') >= 0) {
                    $scope.nSDs = '';
                }
                $scope.error = angular.copy(JSON.stringify(error.data.message));
                $('#error.modal').modal('show');
            })
        });

        $scope.openDetailedLicense = function (data) {
            $scope.currentLicense = angular.copy(data);
            //console.log($scope.currentLicense);
            $('#detailedLicense.modal').modal('show');
            $($(".key.ng-binding.ng-scope")[0]).text("");
        }


        $scope.showModalRequestingLicense = function(service_id, licence_url) {
           $scope.service_id = angular.copy(service_id);       
           $scope.licence_url = angular.copy(licence_url);
           $('#getLicense.modal').modal('show');
         }


         $scope.requestLicense = function(service_id, licence_url) {
           //console.log("$scope.currentNSD.uuid: "+$scope.currentNSD.uuid);
           LicensesServices.requestLicense(ENV, service_id, licence_url)
           .then(function(result) {
             $('#getLicense.modal').modal('hide');   
             $scope.licenseRequest = result.data;
             $('#getLicenseResponse.modal').modal('show');    
           }, function(error) {
             $scope.error = angular.copy(JSON.stringify(error.data.message));
             $('#error.modal').modal('show');   
           })
         }


        $scope.clickPageButton = function (page) {
            var userOffset = page - 1;
            $scope.retrieveNSDs(userOffset);
        }

        $rootScope.$on("reloadLicenses", function(){
            $scope.reload();
        });

        $scope.reload = function () {            
            $scope.retrieveNSDs(0);
        }

        $scope.retrieveNSDs(0);
    }
]);
