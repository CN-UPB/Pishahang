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
 
angular.module('SonataBSS')
    .filter('searchObject', function () {
    return function (items, query) {
        if (!items)
            return false;

        var result = [];
        if (!query) {
            var obj = Object.keys(items);
            for (var i = 0, len = obj.length; i < len; i++) {
                result.push(items[obj[i]]);
            }
            return result;
        }


        function compareStr(stra, strb) {
            stra = ("" + stra).toLowerCase();
            strb = ("" + strb).toLowerCase();
            return stra.indexOf(strb) !== -1;
        }


        angular.forEach(items, function (friend) {
            var keys = Object.keys(friend);
            for (var i = 0, len = keys.length; i < len; i++) {
                if (compareStr(friend[keys[i]], query)) {
                    result.push(friend);
                    break;
                }
            }
        });

        return result;


    }
})

    .filter('orderObjectBy', function () {
    return function (items, field, reverse, groups) {
        var filtered = [];
        angular.forEach(items, function (item) {
            filtered.push(item);
        });

        var parseFieldValue = function (a, field) {

            if (a[field]) {
                if (typeof(a[field]) === "string")
                    return a[field].toUpperCase()
                else
                    return a[field]
            } else if (field && field.indexOf(".") > -1) {
                var fieldsArr = field.split(".");
                var fieldValue = a;
                for (var fieldName in fieldsArr) {

                    if (fieldValue)
                        fieldValue = fieldValue[fieldsArr[fieldName]];
                }
                return fieldValue;
            }
            else {
                return a[field];
            }

        }
        filtered.sort(function (a, b) {

            var upA = parseFieldValue(a, field);
            var upB = parseFieldValue(b, field);

//                var upB = b[field] ? (typeof(b[field]) === "string" ? b[field].toUpperCase() : b[field]) : b[field];


            if (upA > upB) return 1;
            if (upA < upB) return -1;
            return 0;
        });

        if (reverse) filtered.reverse();


        return filtered;
    };
});
