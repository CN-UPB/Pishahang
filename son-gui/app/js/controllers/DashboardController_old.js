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
	
  //GET ALL VIMS
  $scope.selected_vim = 0;
  $scope.vims = new Array();

  $scope.select = {
    choices:[]
  };
            /*value: 0,
            choices: []
        };*/


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
                if(index==0)
                $scope.select.value = element.metric.exported_instance;
              
                $scope.vims.push(element);
                $scope.select.choices.push(element);
                $scope.changeVisibleVim();
              });

          }).then(function(){
            $scope.setVims();

          })
  };

$scope.getVmsState = function(vim){
      
      var vim = vim;

      $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vms_state",
                  "start": ""+ new Date(new Date().getTime() - 3*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]

                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {

            vim.states = data.metrics.result;
            

            google.charts.setOnLoadCallback(drawChart);
      function drawChart() {

        var d = ['State','Number of Vms'];
        var data = new Array();
        data.push(d);

        sum = 0;
        vim.states.forEach(function(state,index){
          data.push([state.metric.state,parseInt(state.values[0][1])]);
          sum+=state.values[0][1];
        });

        var final_data = google.visualization.arrayToDataTable(data);

        var kloptions = {
          title: 'States of the Vms',
          
        };

        var chart = new google.visualization.PieChart(document.getElementById('stateChart_'+vim.id)); 

        chart.draw(final_data, kloptions);



      }

          })

}



$scope.getAllVms = function(vim){

var vim = vim;  

  $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vm_last_update",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]

                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {

            

            vim.all_vms=data;
            vim.all_vms.metrics.result.forEach(function(vm,index){
              
            timestamp = ""+vm.values[0][1]+"000";


              vm.metric.last_updated = timestamp;
             
            });
           $('select').material_select();

          })


}

 
$scope.changeVisibleVim = function(){
  $scope.vims.forEach(function(vim,index){
    if(vim.metric.exported_instance==$scope.select.value)
      vim.visible=1;
    else
      vim.visible=0;
  });

  /**/
}

$scope.setVims = function(){
  $scope.vims.forEach(function(vim,index){
    vim.index_num = index;

    if(index==0)
      vim.visible = 1;
    else
      vim.visible = 0;
    $scope.getAllVms(vim);
    $scope.getVmsState(vim);
  })
  $scope.vims.forEach(function(vim,index){
       $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_totalCoresUsed",
                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            vim.totalCoresUsed = [];
            vim.totalCoresUsed.push(data.metrics.result[0].values);
            
            vim.currently_usedCores = parseFloat(data.metrics.result[0].values[0][1]);              
            console.log(vim.metric.exported_instance+"Cores:"+vim.currently_usedCores);
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
                        "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                          },
                headers : { 'Content-Type': 'application/json' }
               })
                .success(function(data) {
                  vim.maxTotalCores = [];
                  vim.maxTotalCores.push(data.metrics.result[0].values);

                  vim.currently_totalCores = parseFloat(data.metrics.result[0].values[0][1]);              
          
                  $scope.coresChart(vim);
             



                    var data = [
                        ['Label', 'Value'],
                        ['Cores', vim.currently_usedCores],
                        
                      ];
                      var options = {
                        width: 400, height: 120,
                        redFrom: vim.currently_totalCores-2, redTo: vim.currently_totalCores,
                        minorTicks: 25,
                        max:vim.currently_totalCores,
                        chartArea: {
                            left: 10,
                            top: 10,
                            width: '100%',
                            height: 350
                        }
                      };

 

                      $scope.drawGauge(data,options,'vim_cores_gauge_'+vim.id);




                });


          });
            });
          
          
  });
















    $scope.vims.forEach(function(vim,index){
       $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_maxTotalRAMSize",
                  "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            vim.maxTotalRamSize = [];
            vim.maxTotalRamSize.push(data.metrics.result[0].values);
            vim.currently_totalRam = parseFloat(data.metrics.result[0].values[0][1]);
          }).then(function(){

              $scope.vims.forEach(function(vim,index){
               $http({
                  method  : 'POST',
                  url     : $scope.apis.monitoring,
                  data:  {
                          "name": "vim_totalRAMUsed",
                          "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                          "end": ""+new Date().toISOString(),
                          "step": "5m",
                          "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                            },
                  headers : { 'Content-Type': 'application/json' }
                 })
                  .success(function(data) {
                    vim.totalRamUsed = [];
                    vim.totalRamUsed.push(data.metrics.result[0].values);
                    vim.currently_RamUsed = parseFloat(data.metrics.result[0].values[0][1]);
                    
                     var data = [
                        ['Label', 'Value'],
                        ['RAM', vim.currently_RamUsed],
                        
                      ];
                      var options = {
                        width: 400, height: 120,
                        redFrom: vim.currently_totalRam-4000, redTo: vim.currently_totalRam,
                        minorTicks: 25,
                        max:vim.currently_totalRam,
                        chartArea: {
                            left: 10,
                            top: 10,
                            width: '100%',
                            height: 350
                        }
                      };

                      $scope.drawGauge(data,options,'vim_ram_gauge_'+vim.id);


                  
                     $scope.ramChart(vim);  
                  }).then(function(){

                  })
              });
          });
      });

      




  

  $scope.vims.forEach(function(vim,index){
       $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_totalInstancesUsed",
                  "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "5m",
                  "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            vim.totalInstancesUsed = [];
            vim.totalInstancesUsed.push(data.metrics.result[0].values);
            vim.currently_instancesUsed = parseFloat(data.metrics.result[0].values[0][1]);
              
          }).then(function(vim){

            $scope.vims.forEach(function(vim,index){
               $http({
                  method  : 'POST',
                  url     : $scope.apis.monitoring,
                  data:  {
                          "name": "vim_maxTotalInstances",
                          "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                          "end": ""+new Date().toISOString(),
                          "step": "5m",
                          "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                            },
                  headers : { 'Content-Type': 'application/json' }
                 })
                  .success(function(data) {
                    vim.maxTotalInstances = [];
                    vim.maxTotalInstances.push(data.metrics.result[0].values);
                    vim.currently_Totalinstances = parseFloat(data.metrics.result[0].values[0][1]);
                    

                     var data = [
                        ['Label', 'Value'],
                        ['Instances', vim.currently_instancesUsed],
                        
                      ];
                      var options = {
                        width: 400, height: 120,
                        redFrom: 0.8*vim.currently_Totalinstances, redTo: vim.currently_Totalinstances,
                        minorTicks: 25,
                        max:vim.currently_Totalinstances,
                        chartArea: {
                            left: 10,
                            top: 10,
                            width: '100%',
                            height: 350
                        }
                      };

                      $scope.drawGauge(data,options,'vim_instances_gauge_'+vim.id);



                    $scope.instancesChart(vim);
                  });
                      
            });



          });
  });




  $scope.vims.forEach(function(vim,index){
       $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vim_maxTotalFloatingIpsUsed",
                  "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "11m",
                  "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            vim.totalIpsUsed = [];

            if(data.metrics.result.length)
              vim.totalIpsUsed = data.metrics.result[0].values;
            else
              vim.totalIpsUsed = 0;
              


          }).then(function(vim){

            $scope.vims.forEach(function(vim,index){
               $http({
                  method  : 'POST',
                  url     : $scope.apis.monitoring,
                  data:  {
                          "name": "vim_maxTotalFloatingIps",
                          "start": ""+ new Date(new Date().getTime() - 10*60000).toISOString(),
                          "end": ""+new Date().toISOString(),
                          "step": "11m",
                          "labels": [{"labeltag":"exported_instance", "labelid":vim.metric.exported_instance}]
                            },
                  headers : { 'Content-Type': 'application/json' }
                 })
                  .success(function(data) {
                    vim.maxTotalIps = [];
                    if(data.metrics.result.length)
                      vim.maxTotalIps = data.metrics.result[0].values[0][1];
                    else
                      vim.maxTotalIps = 0;
              

                    $scope.IpsChart(vim);
                  });
                      
            });



          });
  });









}



$scope.IpsChart = function(vim){
  
}
$scope.coresChart = function(vim){
      var vim = vim;
 

      google.charts.setOnLoadCallback(drawChart());
      
      function drawChart() {
        var data = [
          ['Time', 'Used', 'Total']];

          vim.totalCoresUsed[0].forEach(function(metric,index){
            
            var timestamp = metric[0].toString();
            timestamp = timestamp.replace('.','');
            timestamp = new Date(parseInt(timestamp));


            data.push(new Array(timestamp,parseFloat(metric[1]),parseFloat(vim.maxTotalCores[0][index][1])));
          });
        

        var options = {
          title: 'Cores',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

    $scope.drawTheChart(data,options,'vim_cores_chart_'+vim.id);


  }




}



$scope.statesChart = function(vim){
      var vim = vim;
      
      google.charts.setOnLoadCallback(drawChart());
      
      function drawChart() {
        var data = [
          ['Time', 'Used', 'Total']];

          vim.totalInstancesUsed[0].forEach(function(metric,index){
            
            var timestamp = metric[0].toString();
            timestamp = timestamp.replace('.','');
            timestamp = new Date(parseInt(timestamp));


            data.push(new Array(timestamp,parseFloat(metric[1]),parseFloat(vim.maxTotalInstances[0][index][1])));
          });
        

        var options = {
          title: 'Instances',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

    $scope.drawTheChart(data,options,'vim_instances_chart_'+vim.id);
  }




}

$scope.instancesChart = function(vim){
      var vim = vim;
      
      google.charts.setOnLoadCallback(drawChart());
      
      function drawChart() {
        var data = [
          ['Time', 'Used', 'Total']];

          vim.totalInstancesUsed[0].forEach(function(metric,index){
            
            var timestamp = metric[0].toString();
            timestamp = timestamp.replace('.','');
            timestamp = new Date(parseInt(timestamp));


            data.push(new Array(timestamp,parseFloat(metric[1]),parseFloat(vim.maxTotalInstances[0][index][1])));
          });
        

        var options = {
          title: 'Instances',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

    $scope.drawTheChart(data,options,'vim_instances_chart_'+vim.id);
  }




}



$scope.ramChart = function(vim){

      var vim = vim;
      
      google.charts.setOnLoadCallback(drawChart());
      
      
      function drawChart() {
        
        var data = [
          ['Time', 'Used', 'Total']];

          vim.totalRamUsed[0].forEach(function(metric,index){
            
            var timestamp = metric[0].toString();
            timestamp = timestamp.replace('.','');
            timestamp = new Date(parseInt(timestamp));


            data.push(new Array(timestamp,parseFloat(metric[1]),parseFloat(vim.maxTotalRamSize[0][index][1])));
          });
        

        var options = {
          title: 'RAM',
          curveType: 'function',
          legend: { position: 'bottom' }
        };

    $scope.drawTheChart(data,options,'vim_ram_chart_'+vim.id);
  }

 
}


$scope.drawTheChart = function(data_array,options,element){

       var data = google.visualization.arrayToDataTable(data_array);
       var options = options;
       var chart = new google.visualization.AreaChart(document.getElementById(element));
       chart.draw(data, options);
       

}

$scope.drawGauge = function(data_array,options,element){

       var data = google.visualization.arrayToDataTable(data_array);
       var options = options;
       var chart = new google.visualization.Gauge(document.getElementById(element));
       chart.draw(data, options);

}


$scope.init = function(){

  $scope.FindAllVims();

  $(document).ready(function(){
    $('ul.tabs').tabs();

  });

}




}]);

$(document).ready(function(){
    
  });