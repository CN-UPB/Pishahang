"use strict";

 angular.module('config', [])

.constant('ENV', {name:'development',apiEndpoint:['http://localhost:1338/mock'],userManagementEnabled:[null],licenseManagementEnabled:[null]})

;