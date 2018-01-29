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

angular.module('Requests')
    .controller('RequestsCtrl', ["$scope", "$rootScope", "RequestsServices", "ENV", "linkHeaderParser", "$localStorage", function ($scope, $rootScope, RequestsServices, ENV, linkHeaderParser, $localStorage) {

        $rootScope.username=$localStorage.currentUser.username;
        $scope.currentRequests = {};
        $scope.offset = 0;
        $scope.limit = 10;

        // retrieve Requests to server
        $scope.retrieveRequests = (function (offset) {
            RequestsServices.retrieveRequests(ENV, offset)
            .then(function (result) {
                $rootScope.Requests = result.data;

                if (JSON.stringify($rootScope.Requests) == "[{}]"){
                    $rootScope.Requests = [];
                }

                //pagination
                var linkHeaderText = result.headers("Link");
                var link = linkHeaderParser.parse(linkHeaderText);
                $scope.totalPages = parseInt(link.last.offset) + 1;
                $scope.limit = parseInt(link.last.limit);
                $scope.totalRecords = $scope.limit * $scope.totalPages;

            }, function (error) {
                if (JSON.stringify(error.data.code).indexOf('401') >= 0) {
                    $rootScope.Requests = '';
                }
                $scope.error = angular.copy(JSON.stringify(error.data.message));
                $('#error.modal').modal('show');
            })
        });

        $scope.retrieveRequests($scope.offset);

        $scope.openDetailedRequest = function (data) {
            $scope.currentRequest = angular.copy(data);
            $('#detailedRequest.modal').modal('show');
            $($(".key.ng-binding.ng-scope")[0]).text("");//.text("Request#" + $scope.currentRequest.id);
        }

        //update data to server
        $scope.updateRequests = function () {
            RequestsServices.updateRequests($scope.currentRequests)
            .then(function (result) {
                for (var key in $rootScope.Requests) {
                    if (result.data.id == $rootScope.Requests[key].id)
                        $rootScope.Requests[key] = result.data;
                }
            }, function (error) {
                $scope.error = angular.copy(JSON.stringify(error.data.message));
                $('#error.modal').modal('show');
            })
        }

        $scope.emptyRequests = function () {
            $scope.currentRequests = {};
        }

        $scope.clickPageButton = function (page) {
            //console.log("button navigation clicked (page "+page+")");
            var offset = page - 1;
            $scope.retrieveRequests(offset);
        }

    }
]);
