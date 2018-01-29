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

SonataApp.controller('AlertsController',['$rootScope','$http','$scope',function($rootScope,$http,$scope){
            
            (function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
           
$scope.minutes = 5;
$scope.refreshAlerts = function(){
  $scope.getAlerts();
}

$scope.getAlerts = function(){
  $scope.minutes = parseInt($scope.minutes);
  if($scope.minutes>150){
    alert('You can not have alerts for this period of time. Please select a smaller range');
  }else{
  $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "ALERTS",
                  "start": ""+ new Date(new Date().getTime() - $scope.minutes*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "1s",
                  "labels": [{}]

                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
              console.log(data);
              $scope.alerts = data.metrics.result;
              $scope.alerts = new Array();
              
              data.metrics.result.forEach(function(alert,index){
                  
                  var al = alert.metric;
                  

                  alert.values.reverse();
                  var timest = 0;
                  alert.values.forEach(function(value,index){
                    if(timest==0){
                      if(value[1]==1){
                      timest = value[0];
                      
                      }  
                    }
                    

                     /*al.value = 1;
                     al.timestamp = timest;*/
                      al.value     = alert.values[alert.values.length-1][1];
                      al.timestamp = alert.values[alert.values.length-1][0];

                  });

                  if(timest!=0){
                    al.value     = 1;
                    al.timestamp = timest;  
                  }
                  else 
                    al.value = 0;

                  

                  if(al.alertname.indexOf('cpu') !== -1 && !angular.isUndefined(al.core)){
                    al.alertname+= " core: "+al.core;
                  }
                  
                  
                  al.timestamp = al.timestamp.toString();
                  al.timestamp = al.timestamp.replace('.','');
                  
                  
                  if(al.timestamp.length==12)
                    al.timestamp=al.timestamp+'0';
                  else if(al.timestamp.length==11)
                    al.timestamp=al.timestamp+'00';
                  else if(al.timestamp.length==10)
                    al.timestamp = al.timestamp+'000';


                  
                  
                  al.timestamp = new Date(parseInt(al.timestamp));
                  
                  if(al.value==1 && al.alertstate=='firing'){
                    
                    if(al.exported_job=='vnf'){
                      al.next_state = '/vnf/'+al.id;
                      $scope.getAlertVNFName(al);
                    }
                    else if(al.exported_job=='vm'){
                      al.next_state = '/vm/'+al.id;
                      $scope.getAlertVMName(al);
                    }
                    else if(al.exported_job=='container' || al.exported_job=='containers'){
                      al.next_state = '/container/'+al.id;
                      $scope.getAlertContainerName(al);
                    }
                    else{
                      al.next_state = '/alerts';
                      al.name = '-';
                    }

                    $

                    $scope.alerts.push(al);

                  }
              });



          });
        }
}
  
  $scope.getAlertVMName = function(al){
     $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vm_mem_perc",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "10m",
                  "labels": [{"labeltag":"id","labelid":al.id}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            al.name = data.metrics.result[0].metric.exported_instance;       
            
          });
  }
  $scope.getAlertVNFName = function(al){
    $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vm_mem_perc",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "10m",
                  "labels": [{"labeltag":"id","labelid":al.id}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            al.name = data.metrics.result[0].metric.exported_instance;       
            
          });
    
  }
  $scope.getAlertContainerName = function(al){
    $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "cnt_mem_perc",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "10m",
                  "labels": [{"labeltag":"id","labelid":al.id}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            
            al.name = data.metrics.result[0].metric.exported_instance;
        
            
          });
  }


    $scope.changeState = function(next_state){
      location.hash="#"+next_state;
    }
    $scope.init = function(){
        $scope.getAlerts();
        setInterval(function() {
          $scope.getAlerts();
        }, 6000);
    }
      



           
}]);