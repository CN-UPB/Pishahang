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
    .controller('UserLicensesCtrl', ["$scope", "$rootScope", "$localStorage", "UserLicensesServices", "ENV", "linkHeaderParser", function ($scope, $rootScope, $localStorage, UserLicensesServices, ENV, linkHeaderParser) {

        $rootScope.username=$localStorage.currentUser.username;
        $scope.userLicenses = {};
        $scope.userLicOffset = 0;
        $scope.userLicLimit = 10;
        $scope.user_name = $localStorage.currentUser.username;

        // retrieve Requests to server
        $scope.retrieveUserLicenses = (function (offset) {
            UserLicensesServices.retrieveUserLicenses(ENV, offset)
            .then(function (result) {
                $scope.userLicenses = result.data;

                if (JSON.stringify($scope.userLicenses) == "[{}]"){
                    $scope.userLicenses = [];
                }

                //pagination
                var linkHeaderText = result.headers("Link");
                var link = linkHeaderParser.parse(linkHeaderText);
                $scope.totalUserLicPages = parseInt(link.last.offset) + 1;
                $scope.userLiclimit = parseInt(link.last.limit);
                $scope.totalUserLicRecords = $scope.userLiclimit * $scope.totalUserLicPages;

            }, function (error) {
                if (JSON.stringify(error.data.code).indexOf('401') >= 0) {
                    $scope.userLicenses = '';
                }
                $scope.error = angular.copy(JSON.stringify(error.data.message));
                $('#error.modal').modal('show');
            })
        });

        

        $scope.openDetailedUserLicense = function (data) {
            $scope.currentUserLicense = angular.copy(data);
            $('#detailedUserLicense.modal').modal('show');
            $($(".key.ng-binding.ng-scope")[0]).text("");//.text("License#" + $scope.currentUserLicense.license_id);
        }

        $scope.clickUserLicPageButton = function (page) {
            var userLicOffset = page - 1;
            $scope.retrieveUserLicenses(userLicOffset);
        }

        $rootScope.$on("reloadUserLicenses", function(){
            $scope.reload();
        });

        $scope.reload = function () {
            $scope.retrieveUserLicenses(0);
        }

        $scope.retrieveUserLicenses(0);
    }
]);
