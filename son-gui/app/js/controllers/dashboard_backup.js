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

SonataApp.controller('DashboardController',['$rootScope','$scope','$routeParams','$location','$http',function($rootScope,$scope, $routeParams, $location, $http){
(function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
	
  
  
  $scope.vims = new Array();

  $scope.select = {
    choices:[]
  };
    

  $scope.FindAllVims = function(){

     $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_maxTotalInstances",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "10m",
                  "labels": []
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
              
              data.metrics.result.forEach(function(element,index){
                element.id = index;       
                element.vim_tenant = element.metric.vim_tenant;         
                $scope.vims.push(element);              
                $scope.select.choices.push(element.metric.exported_instance);
                /*if(index==0){
                  $scope.selected_vim = {};
                  $scope.selected_vim.name = element.metric.exported_instance;
                  
                }*/
              });



          }).then(function(){
            

            /*setTimeout(function(){
              if($scope.v)
              $scope.changeVisibleVim($scope.vims[0].metric.exported_instance);  
            },3500);*/
            

          })
  };




$scope.setFloatingIps = function(){
  $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_maxTotalFloatingIpsUsed",
                  "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "11m",
                  "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            $scope.selected_vim.totalIpsUsed = [];

            if(data.metrics.result.length)
              $scope.selected_vim.totalIpsUsed = data.metrics.result[0].values;
            else
              $scope.selected_vim.totalIpsUsed = 0;
              


          }).then(function(){

            
               $http({
                  method  : 'POST',
                  url     : $scope.apis.monitoring,
                  data:  {
                          "name": "vim_maxTotalFloatingIps",
                          "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                          "end": ""+new Date().toISOString(),
                          "step": "11m",
                          "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                            },
                  headers : { 'Content-Type': 'application/json' }
                 })
                  .success(function(data) {
                    $scope.selected_vim.maxTotalIps = [];
                    if(data.metrics.result.length)
                      $scope.selected_vim.maxTotalIps = data.metrics.result[0].values[0][1];
                    else
                      $scope.selected_vim.maxTotalIps = 0;
                  });


          });
  
}

$scope.getRamGauge = function(){
  $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_maxTotalRAMSize",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {

            $scope.selected_vim.maxTotalRamSize.push(data.metrics.result[0].values);
            $scope.selected_vim.currently_totalRam = parseFloat(data.metrics.result[0].values[0][1]);
          }).then(function(){

              
               $http({
                  method  : 'POST',
                  url     : $scope.apis.monitoring,
                  data:  {
                          "name": "vim_totalRAMUsed",
                          "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                          "end": ""+new Date().toISOString(),
                          "step": "5m",
                          "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                            },
                  headers : { 'Content-Type': 'application/json' }
                 })
                  .success(function(data) {
                    
                    $scope.selected_vim.totalRamUsed.push(data.metrics.result[0].values);
                    $scope.selected_vim.currently_RamUsed = parseFloat(data.metrics.result[0].values[0][1]);
                    
                     var data = [
                        ['Label', 'Value'],
                        ['RAM', $scope.selected_vim.currently_RamUsed],
                        
                      ];
                      var options = {
                        width: 400, height: 120,
                        redFrom: $scope.selected_vim.currently_totalRam-4000, redTo: $scope.selected_vim.currently_totalRam,
                        minorTicks: 25,
                        max:$scope.selected_vim.currently_totalRam,
                        chartArea: {
                            left: 10,
                            top: 10,
                            width: '100%',
                            height: 350
                        }
                      };                    

                      
                      $scope.drawGauge(data,options,'vim_ram_gauge');


                  
                  
                  }).then(function(){
                    $scope.getRamGraph();
                  })
              
          });
 }

$scope.waitForElementToDisplay = function(selector,time) {
        if(document.querySelector(selector)!=null) {
            return true;
        }
        else {
            setTimeout(function() {
                waitForElementToDisplay(selector, 200);
            }, 200);
        }
    }
 $scope.getRamGraph = function(){
      
      google.charts.setOnLoadCallback(drawChart());      
      
      function drawChart() {
        
        var data = [
          ['Time', 'Used', 'Total']];
          
          $scope.selected_vim.totalRamUsed[0].forEach(function(metric,index){
            
            var timestamp = metric[0].toString();
            timestamp = timestamp.replace('.','');
            
            if(timestamp.length==11)
              timestamp = timestamp+'00';
            else if(timestamp.length==10)
              timestamp = timestamp+'000';
            else if(timestamp.length==12)
                    timestamp=timestamp+'0';
            
            timestamp = new Date(parseInt(timestamp));
            /*timestamp = $filter('date')(timestamp, "hh:mm:ss");*/
            


            data.push(new Array(timestamp,parseFloat(metric[1]),parseFloat($scope.selected_vim.maxTotalRamSize[0][index][1])));
          });
        

        var options = {
          title: 'RAM',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

    $scope.drawTheChart(data,options,'vim_ram_chart');
  }
}

$scope.drawTheChart = function(data_array,options,element){

       var data = google.visualization.arrayToDataTable(data_array);
       var options = options;
       var chart = new google.visualization.AreaChart(document.getElementById(element));
       chart.draw(data, options);
       

}


$scope.getCoresGauge = function(){
  $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_totalCoresUsed",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            $scope.selected_vim.totalCoresUsed = [];
            $scope.selected_vim.totalCoresUsed.push(data.metrics.result[0].values);
            
            $scope.selected_vim.currently_usedCores = parseFloat(data.metrics.result[0].values[0][1]);              
            
          }).then(function(){

              $scope.vims.forEach(function(vim,index){
             $http({
                method  : 'POST',
                url     : $scope.apis.monitoring,
                data:  {
                        "name": "vim_maxTotalCores",
                        "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                        "end": ""+new Date().toISOString(),
                        "step": "5m",
                        "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                          },
                headers : { 'Content-Type': 'application/json' }
               })
                .success(function(data) {
                  $scope.selected_vim.maxTotalCores = [];
                  $scope.selected_vim.maxTotalCores.push(data.metrics.result[0].values);

                  $scope.selected_vim.currently_totalCores = parseFloat(data.metrics.result[0].values[0][1]);              
          
                  /*$scope.coresChart(vim);*/
             



                    var data = [
                        ['Label', 'Value'],
                        ['Cores', $scope.selected_vim.currently_usedCores],
                        
                      ];
                      var options = {
                        width: 400, height: 120,
                        redFrom: $scope.selected_vim.currently_totalCores-2, redTo: $scope.selected_vim.currently_totalCores,
                        minorTicks: 25,
                        max:$scope.selected_vim.currently_totalCores,
                        chartArea: {
                            left: 10,
                            top: 10,
                            width: '100%',
                            height: 350
                        }
                      };

                          $scope.drawGauge(data,options,'vim_cores_gauge');
                          $scope.coresChart();

                      




                });


          });
            });
}
$scope.coresChart = function(){

 

      google.charts.setOnLoadCallback(drawChart());
      
      function drawChart() {
        var data = [
          ['Time', 'Used', 'Total']];

          $scope.selected_vim.totalCoresUsed[0].forEach(function(metric,index){
            
            var timestamp = metric[0].toString();
            timestamp = timestamp.replace('.','');
            if(timestamp.length==12)
                    timestamp=timestamp+'0';
            timestamp = new Date(parseInt(timestamp));


            data.push(new Array(timestamp,parseFloat(metric[1]),parseFloat($scope.selected_vim.maxTotalCores[0][index][1])));
          });
        

        var options = {
          title: 'Cores',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

    $scope.drawTheChart(data,options,'vim_cores_chart');


  }
}

$scope.getInstancesGauge = function(){
  $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_totalInstancesUsed",
                  "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            $scope.selected_vim.totalInstancesUsed = [];
            $scope.selected_vim.totalInstancesUsed.push(data.metrics.result[0].values);
            $scope.selected_vim.currently_instancesUsed = parseFloat(data.metrics.result[0].values[0][1]);
              
              

          }).then(function(){

            
               $http({
                  method  : 'POST',
                  url     : $scope.apis.monitoring,
                  data:  {
                          "name": "vim_maxTotalInstances",
                          "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                          "end": ""+new Date().toISOString(),
                          "step": "5m",
                          "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]
                            },
                  headers : { 'Content-Type': 'application/json' }
                 })
                  .success(function(data) {
                    $scope.selected_vim.maxTotalInstances = [];
                    $scope.selected_vim.maxTotalInstances.push(data.metrics.result[0].values);
                    $scope.selected_vim.currently_Totalinstances = parseFloat(data.metrics.result[0].values[0][1]);
                    

                     var data = [
                        ['Label', 'Value'],
                        ['Instances', $scope.selected_vim.currently_instancesUsed],
                        
                      ];
                      var options = {
                        width: 400, height: 120,
                        redFrom: 0.8*$scope.selected_vim.currently_Totalinstances, redTo: $scope.selected_vim.currently_Totalinstances,
                        minorTicks: 25,
                        max:$scope.selected_vim.currently_Totalinstances,
                        chartArea: {
                            left: 10,
                            top: 10,
                            width: '100%',
                            height: 350
                        }
                      };

                      $scope.drawGauge(data,options,'vim_instances_gauge');



                    $scope.instancesChart();
                  });
                      
            



          });
}
$scope.instancesChart = function(){

      google.charts.setOnLoadCallback(drawChart());
      
      function drawChart() {
        var data = [
          ['Time', 'Used', 'Total']];

          $scope.selected_vim.totalInstancesUsed[0].forEach(function(metric,index){
            
            var timestamp = metric[0].toString();
            timestamp = timestamp.replace('.','');
            if(timestamp.length==12)
                    timestamp=timestamp+'0';
            timestamp = new Date(parseInt(timestamp));


            data.push(new Array(timestamp,parseFloat(metric[1]),parseFloat($scope.selected_vim.maxTotalInstances[0][index][1])));
          });
        

        var options = {
          title: 'Instances',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

    $scope.drawTheChart(data,options,'vim_instances_chart');
  }






}

$scope.openVMInfo = function(service){     

  

      service.networks = [];
      if(angular.isDefined(service.metric.network_1)){
        service.networks.push(service.metric.network_1);
      }
      if(angular.isDefined(service.metric.network_2)){
        service.networks.push(service.metric.network_2);
      }
      if(angular.isDefined(service.metric.network_3)){
        service.networks.push(service.metric.network_3);
      }
            
             $('#modal_vm').openModal();
             $scope.modals = {};
             $scope.modals.content = {};
             $scope.modals.content = service.metric;
             $scope.modals.networks = service.networks;
              
}


$scope.getVms = function(){
      
      $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vm_last_update",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]

                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {

            console.log("VMS");
            console.log(data);

            $scope.selected_vim.all_vms=data;
            $scope.selected_vim.all_vms.metrics.result.forEach(function(vm,index){
              
              timestamp = ""+vm.values[0][1]+"000";
              vm.metric.last_updated = timestamp;
             
            });

          })
}

$scope.getStates = function(){


      $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vms_state",
                  "start": ""+ new Date(new Date().getTime() - 3*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":$scope.selected_vim.name}]

                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {

            $scope.selected_vim.states = data.metrics.result;            

            google.charts.setOnLoadCallback(drawChart);

      function drawChart() {

        var d = ['State','Number of Vms'];
        var data = new Array();
        data.push(d);

        sum = 0;
        $scope.selected_vim.states.forEach(function(state,index){
          data.push([state.metric.state,parseInt(state.values[0][1])]);
          $scope.sum+=state.values[0][1];
        });
        
        var final_data = google.visualization.arrayToDataTable(data);

        var kloptions = {
          title: 'States of the VMs',          
        };

        var chart = new google.visualization.PieChart(document.getElementById('stateChart')); 

        chart.draw(final_data, kloptions);



      }

          })
}

$scope.VimSelected = function(){
  
  
  $scope.setFloatingIps();
  $scope.getRamGauge();
  $scope.getCoresGauge();
  $scope.getInstancesGauge();
  $scope.getVms();
  $scope.getStates();
  $scope.setSelectedClass();

  

}
$scope.changeVisibleVim = function(name){
  $scope.selected_vim = {
    name:name,
     totalRamUsed:[],
     maxTotalRamSize:[]

  };
  
  $scope.VimSelected();
}

$scope.setSelectedClass = function(){
  $scope.vims.forEach(function(vim,index){
    if(vim.metric.exported_instance==$scope.selected_vim.name)
      vim.selected_visible='active';
    else
      vim.selected_visible='';
  })
}
$scope.init = function(){

  $scope.FindAllVims();

 
}

$scope.drawGauge = function(data_array,options,element){
        console.log(data_array);
       var data = google.visualization.arrayToDataTable(data_array);
       var options = options;
       var chart = new google.visualization.Gauge(document.getElementById(element));
       chart.draw(data, options);

}




}]);






































































