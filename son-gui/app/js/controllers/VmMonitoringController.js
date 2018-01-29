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

SonataApp.controller('VmMonitoring',['$rootScope','$scope','$routeParams','$location','$http','$interval','Monitoring',function($rootScope,$scope, $routeParams, $location, $http,$interval,Monitoring){
	
  $scope.vm = {};
  $scope.a_metrics = [];
  $scope.vm.currentMemoryUsage = 0;
  $scope.vm.currentCPUUsage = 0;
	$scope.current_time = new Date();
  $scope.ten_m_before = new Date($scope.current_time.getTime() - 20*60000);
  $scope.settings_modal = {};
  $scope.intervals = [];
  $scope.settings_modal.title = "Chart configuration";

  $scope.potential_timeranges = [];
  $scope.potential_timeranges.push({id:1,range:'1min',val:1});
  $scope.potential_timeranges.push({id:2,range:'5mins',val:5});
  $scope.potential_timeranges.push({id:3,range:'10mins',val:10});
  $scope.potential_timeranges.push({id:4,range:'15mins',val:15});
  $scope.potential_timeranges.push({id:5,range:'20mins',val:20});
  $scope.potential_timeranges.push({id:6,range:'1hour',val:60});
  $scope.potential_timeranges.push({id:7,range:'24hours',val:1440});


  $scope.potential_step = [];
  $scope.potential_step.push({id:1,step:'1sec',val:'1s'});
  $scope.potential_step.push({id:2,step:'15sec',val:'15s'});
  $scope.potential_step.push({id:3,step:'30sec',val:'30s'});
  $scope.potential_step.push({id:4,step:'1min',val:'1m'});
  $scope.potential_step.push({id:5,step:'5min',val:'5m'});
  $scope.potential_step.push({id:6,step:'10min',val:'10m'});

  


  $scope.boxes = [];


$scope.newChartBtn = function(){

  var thebox = {
    id:'box_'+parseInt($scope.custom_boxes.length+1)+"_"+parseInt(Math.random(10000)*100000),
    class:'col s12 m6',
    title:'',
    measurement_name:''
  };
  $scope.configureBox(thebox);
}

$scope.configureBox = function(box){
  $scope.selected_box = {};
  $scope.selected_box = box;
  $('#settings_modal').openModal();
}


$scope.saveBoxConfiguration = function(){
  
  $scope.selected_box.measurement = $scope.settings_modal.measurement;
  $scope.selected_box.time_range  = $scope.settings_modal.time_range;
  $scope.selected_box.step        = $scope.settings_modal.step;
  
  $scope.addNewChart($scope.selected_box);
}

$scope.addNewChart = function(new_chart){

  //Local Storage Feauture
  $scope.custom_boxes.push(new_chart);
  $scope.custom_boxes.forEach(function(e,i){
    $scope.custom_boxes[i] = JSON.stringify($scope.custom_boxes[i]);
  });
  $rootScope.setStorage('sonata_custom_charts_vm_'+$routeParams.name,JSON.stringify($scope.custom_boxes));
  $scope.loadCustomBoxes();
  //End Local Storage Feaute
}  


$scope.loadCustomBoxes = function(){
      
      $scope.custom_boxes = [];
      $scope.custom_boxes = $rootScope.getStorage('sonata_custom_charts_vm_'+$routeParams.name);
      $scope.custom_boxes = JSON.parse($scope.custom_boxes);
      console.log($scope.custom_boxes);
      
      if(!$rootScope.checkIfNull($scope.custom_boxes) && $scope.custom_boxes.length>0){
        
        $scope.custom_boxes.forEach(function(e,i){
          $scope.custom_boxes[i] = JSON.parse(e);
        });
        $scope.appearCustomCharts();
      }else{
        $scope.custom_boxes = [];
      }
}

$scope.appearCustomCharts = function(){
  $scope.custom_boxes.forEach(function(e,i){
    $scope.fillnewBox(e);
  })
}


$scope.updateBox = function(box){
  $scope.fillnewBox(box);
}
$scope.removeBox = function(box){
  console.log(box);

  for (var i =0; i < $scope.boxes.length; i++){
    if ($scope.boxes[i].id === box.id) {
      $scope.boxes.splice(i,1);
      console.log("i found it:"+$scope.boxes[i].id);
      console.log($scope.boxes);
      break;
   }
  }
   


   for (var i =0; i < $scope.custom_boxes.length; i++){
    if ($scope.custom_boxes[i].id === box.id) {
      $scope.custom_boxes.splice(i,1);
      $scope.custom_boxes.forEach(function(e,i){
        $scope.custom_boxes[i] = JSON.stringify($scope.custom_boxes[i]);
      });
      $rootScope.setStorage('sonata_custom_charts_vm_'+$routeParams.name,JSON.stringify($scope.custom_boxes));
      $scope.loadCustomBoxes();
   }
   }
   

}







$scope.getAllPotentialMeasurements = function(){
  $scope.potential_graphs = [];
  
  $http({
          method  : 'GET',
          url     : $scope.apis.monitoring_list,
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
            data.metrics.forEach(function(metric,index){
              if(metric.startsWith('vm_'))
                $scope.potential_graphs.push(metric);
            })
           
            
          });
}
$scope.getAllPotentialMeasurements();


$scope.fillnewBox = function(box){

  var tt = $scope.getObjById($scope.potential_timeranges, parseInt(box.time_range));              
  var st = $scope.getObjById($scope.potential_step, parseInt(box.step));

            var start = new Date(new Date().getTime() - parseInt(tt.val)*60000).toISOString();
        var end   = new Date().toISOString();
        var name  = box.measurement;
        var step  = st.val;

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){
              
                    $scope.data = [];
                    if(data.data[0]){
                     data.data[0].values.forEach(function(element, index) {
          
                            var timestamp = $rootScope.FixTimestamp(element[0]);
                            $scope.data.push([timestamp,parseFloat(element[1])]);
                       });


                     $scope.g_charts.push(Highcharts.stockChart(box.id, {
                              chart: {
                                  zoomType: 'x'
                              },
                              rangeSelector: {
                                  enabled: false
                              },
                              navigator: {
                                  enabled: false
                              },
                              title: {
                                  text: box.measurement
                              },
                              subtitle: {
                                  text: document.ontouchstart === undefined ?
                                          'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
                              },
                              xAxis: {
                                  type: 'datetime'
                              },
                              yAxis: {
                                  title: {
                                      text: 'Values'
                                  }
                              },
                              legend: {
                                  enabled: false
                              },
                              credits: {
                                enabled: false
                              },
                              plotOptions: {
                                  area: {
                                      fillColor: {
                                          linearGradient: {
                                              x1: 0,
                                              y1: 0,
                                              x2: 0,
                                              y2: 1
                                          },
                                          stops: [
                                              [0, '#262B33'],
                                              [1, '#FFFFFF']
                                          ]
                                      },
                                      marker: {
                                          radius: 2
                                      },
                                      lineWidth: 1,
                                      states: {
                                          hover: {
                                              lineWidth: 1
                                          }
                                      },
                                      threshold: null
                                  }
                              },

                              series: [{
                                  type: 'area',
                                  color: '#454e5d',
                                  name: box.measurement,
                                  data: $scope.data
                              }]
                          }));
                    }else{
                      
                      $('#'+box.id).html('No data Available for '+box.measurement);
                
                     }
                });
}





$scope.getObjById = function(arr, id) {
    for (var d = 0, len = arr.length; d < len; d += 1) {
        if (arr[d].id === id) {
            return arr[d];
        }
    }
}




$scope.getVM = function(){

        var end   = new Date().toISOString();
        var start = new Date(new Date().getTime() - 20*60000).toISOString();
        var name  = "vm_mem_perc";
        var step  = "10m";

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){
            
           $scope.vm.exported_instance = data.data[0].metric.exported_instance;
           $scope.vm.instance          = data.data[0].metric.instance;
           $scope.vm.group= data.data[0].metric.group;
           $scope.vm.id = data.data[0].metric.id;
           $scope.getContainers();
        });
}

$scope.getCurrentMemory = function(){
  
        var start = new Date().toISOString();
        var end   = new Date().toISOString();
        var name  = "vm_mem_perc";
        var step  = "10m";

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){
           $scope.vm.currentMemoryUsage = 100-data.data[0].values[0][1];
        });

}

$scope.getCurrentCPU = function(){
        
        var start = new Date().toISOString();
        var end   = new Date().toISOString();
        var name  = "vm_mem_perc";
        var step  = "1m";

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){
           $scope.vm.currentCPUUsage = data.data[0].values[0][1];
        });

}


$scope.getCPU_History = function(){
  
   $http({
          method  : 'POST',
          url     : $scope.apis.monitoring,
          data:  {
                  "name": "vm_cpu_perc",

                  "start": ""+ new Date(new Date().getTime() - 20*60000).toISOString(),
                  "end": ""+new Date().toISOString(),
                  "step": "1m",
                  "labels": [{"labeltag":"id","labelid":$routeParams.name}]
                    },
          headers : { 'Content-Type': 'application/json' }
         })
          .success(function(data) {
       
            
          });
}


$scope.historyCPU = function(){

 var end = new Date().toISOString();
        var start = new Date(new Date().getTime() - 20*60000).toISOString();
        var name = "vm_cpu_perc";
        var step = "1s";
 
        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id"+
                  "&labels[][labelid]=vm"+
                  "&labels[][labeltag]=exported_job";;

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){

          $scope.prdata = [];

          data.data[0].values.forEach(function(element, index) {
           
            var timestamp = $rootScope.FixTimestamp(element[0]);
            $scope.prdata.push([timestamp,parseFloat(element[1])]);
           
          });

                       $scope.g_charts.push(Highcharts.stockChart('cpu_chart_new', {
                              chart: {
                                  zoomType: 'x',
                                  events: {
                                      load: function () {
                                          
                                          var series = this.series[0];
                                          $scope.intervals.push($interval(function () {

                                              var end = new Date().toISOString();
                                              var start = end;
                                              var name = "vm_cpu_perc";
                                              var step = "10s";
                                       
                                              var url = $rootScope.apis.monitoring_data+
                                                        "?end="+end+
                                                        "&start="+start+
                                                        "&name="+name+
                                                        "&step="+step+
                                                        "&labels[][labelid]="+$routeParams.name+
                                                        "&labels[][labeltag]=id"+
                                                        "&labels[][labelid]=vm"+
                                                        "&labels[][labeltag]=exported_job";;

                                              var m = Monitoring.getData(encodeURI(url));
                                              m.then(function(data){

                                                  $scope.vm.currentCPUUsage = data.data[0].values[0][1];

                                                
                                                    var y = data.data[0].values[0][1];
                                                    var x = data.data[0].values[0][0];
                                                    var timestamp = $rootScope.FixTimestamp(x);

                                                      series.addPoint([timestamp, parseFloat(y)], true, true);
                               
                                              });


                                          }, 5000));

                                      }
                                    }
                              },
                              rangeSelector: {
                                  enabled: false
                              },
                              navigator: {
                                  enabled: false
                              },
                              title: {
                                  text: 'CPU usage over time'
                              },
                              subtitle: {
                                  text: document.ontouchstart === undefined ?
                                          'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
                              },
                              xAxis: {
                                  type: 'datetime'
                              },
                              yAxis: {
                                  title: {
                                      text: 'CPU %'
                                  }
                              },
                              legend: {
                                  enabled: false
                              },
                              credits: {
                                enabled: false
                              },
                              plotOptions: {
                                  area: {
                                      fillColor: {
                                          linearGradient: {
                                              x1: 0,
                                              y1: 0,
                                              x2: 0,
                                              y2: 1
                                          },
                                          stops: [
                                              [0, '#262B33'],
                                              [1, '#FFFFFF']
                                          ]
                                      },
                                      marker: {
                                          radius: 2
                                      },
                                      lineWidth: 1,
                                      states: {
                                          hover: {
                                              lineWidth: 1
                                          }
                                      },
                                      threshold: null
                                  }
                              },

                              series: [{
                                  type: 'area',
                                  color: '#454e5d',
                                  name: 'CPU',
                                  data: $scope.prdata
                              }]
                          }));
          });

}



$scope.historyRAM = function(){


        var end = new Date().toISOString();
    var start = new Date(new Date().getTime() - 20*60000).toISOString();
    var name = "vm_mem_perc";
    var step = "1s";

    var url = $rootScope.apis.monitoring_data+
              "?end="+end+
              "&start="+start+
              "&name="+name+
              "&step="+step+
              "&labels[][labelid]="+$routeParams.name+
              "&labels[][labeltag]=id"+
              "&labels[][labelid]=vm"+
              "&labels[][labeltag]=exported_job";;

    var m = Monitoring.getData(encodeURI(url));
    m.then(function(data){

            $scope.ramdata = [];                                        
            
            data.data[0].values.forEach(function(element, index) {

              var timestamp = $rootScope.FixTimestamp(element[0]);
              $scope.ramdata.push([timestamp,parseFloat(100-element[1])]);

             });

                      $scope.g_charts.push(Highcharts.stockChart('ram_chart_new', {
                              chart: {
                                  zoomType: 'x',
                                  events: {
                                      load: function () {

                                          
                                          var series = this.series[0];
                                          $scope.intervals.push($interval(function () {


                                            var end = new Date().toISOString();
                                            var start = new Date().toISOString();
                                            var name = "vm_mem_perc";
                                            var step = "10s";

                                            var url = $rootScope.apis.monitoring_data+
                                                      "?end="+end+
                                                      "&start="+start+
                                                      "&name="+name+
                                                      "&step="+step+
                                                      "&labels[][labelid]="+$routeParams.name+
                                                      "&labels[][labeltag]=id"+
                                                      "&labels[][labelid]=vm"+
                                                      "&labels[][labeltag]=exported_job";;

                                            var m = Monitoring.getData(encodeURI(url));
                                            m.then(function(data){ 
                                              
                                                if(data.data.length>0){
                                                  var y = 100-data.data[0].values[0][1];
                                                    $scope.vm.currentMemoryUsage = parseFloat(y);
                                                    var timestamp = $rootScope.FixTimestamp(data.data[0].values[0][0]);
                                                   series.addPoint([timestamp, parseFloat(y)], true, true);
                                                }
                                                    

                                            })

                                          }, 5000));                         


                                      }
                                    }
                              },
                              rangeSelector: {
                                  enabled: false
                              },
                              navigator: {
                                  enabled: false
                              },
                              title: {
                                  text: 'Memory usage over time'
                              },
                              subtitle: {
                                  text: document.ontouchstart === undefined ?
                                          'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
                              },
                              xAxis: {
                                  type: 'datetime'
                              },
                              yAxis: {
                                  title: {
                                      text: 'RAM %'
                                  }
                              },
                              legend: {
                                  enabled: false
                              },
                              credits: {
                                enabled: false
                              },
                              plotOptions: {
                                  area: {
                                      fillColor: {
                                          linearGradient: {
                                              x1: 0,
                                              y1: 0,
                                              x2: 0,
                                              y2: 1
                                          },
                                          stops: [
                                              [0, '#262B33'],
                                              [1, '#FFFFFF']
                                          ]
                                      },
                                      marker: {
                                          radius: 2
                                      },
                                      lineWidth: 1,
                                      states: {
                                          hover: {
                                              lineWidth: 1
                                          }
                                      },
                                      threshold: null
                                  }
                              },

                              series: [{
                                  type: 'area',
                                  color: '#454e5d',
                                  name: 'RAM',
                                  data: $scope.ramdata
                              }]
                          }));
          });
}




$scope.drawGaugesRAM = function(){
   google.charts.setOnLoadCallback(drawChart);
      function drawChart() {

        var data = google.visualization.arrayToDataTable([
          ['Label', 'Value'],
          ['Memory', parseFloat($scope.vm.currentMemoryUsage)],
        ]);

        var options = {
          width: 400, height: 120,
          redFrom: 90, redTo: 100,
          yellowFrom:75, yellowTo: 90,
          minorTicks: 5
        };

        var chart = new google.visualization.Gauge(document.getElementById('vRAMschart'));
        chart.draw(data, options);
        $scope.intervals.push($interval(function() {
          $scope.getCurrentMemory();          
          data.setValue(0, 1, parseFloat($scope.vm.currentMemoryUsage));
          chart.draw(data, options);
        }, 4000));
       
       
      }
}

$scope.drawGauges = function(){
   google.charts.setOnLoadCallback(drawChart);
      function drawChart() {

        var data = google.visualization.arrayToDataTable([
          ['Label', 'Value'],          
          ['CPU', parseFloat($scope.vm.currentCPUUsage)]
        ]);

        var options = {
          width: 400, height: 120,
          redFrom: 90, redTo: 100,
          yellowFrom:75, yellowTo: 90,
          minorTicks: 5
        };

        var chart = new google.visualization.Gauge(document.getElementById('vCPUschart'));
        chart.draw(data, options);

        $scope.intervals.push($interval(function() {
          $scope.getCurrentMemory();          
          data.setValue(0, 1, parseFloat($scope.vm.currentCPUUsage));
          chart.draw(data, options);
        }, 4000));       
      }
}


$scope.historyHardDisk = function(){

        var end = new Date().toISOString();
              var start = new Date(new Date().getTime() - 150*60000).toISOString();
              var name = "vm_disk_usage_perc";
              var step = "5m";

              var url = $rootScope.apis.monitoring_data+
                        "?end="+end+
                        "&start="+start+
                        "&name="+name+
                        "&step="+step+
                        "&labels[][labelid]="+$routeParams.name+
                        "&labels[][labeltag]=id"+
                        "&labels[][labelid]=vm"+
                        "&labels[][labeltag]=exported_job";;

              var m = Monitoring.getData(encodeURI(url));
              m.then(function(data){
                      
                     //  var y = 100-data.data[0].values[0][1];
                     //  $scope.vm.currentMemoryUsage = parseFloat(y);
                     //  var timestamp = $rootScope.FixTimestamp(data.data[0].values[0][0]);
                     // series.addPoint([timestamp, parseFloat(y)], true, true);

                     $scope.vm.disk_total = 0;
                     
                     data.data.forEach( function(element, index) {
                      var m= element.metric.file_system;
                        if(m.startsWith("/dev")){
                          $scope.vm.disk_total = parseFloat(element.values[0][1]);
                            
                            var end = new Date().toISOString();
                            var start = new Date(new Date().getTime() - 150*60000).toISOString();
                            var name = "vm_disk_usage_perc";
                            var step = "5m";

                            var url = $rootScope.apis.monitoring_data+
                                      "?end="+end+
                                      "&start="+start+
                                      "&name="+name+
                                      "&step="+step+
                                      "&labels[][labelid]="+$routeParams.name+
                                      "&labels[][labeltag]=id"+
                                      "&labels[][labelid]=vm"+
                                      "&labels[][labeltag]=exported_job";;

                            var m = Monitoring.getData(encodeURI(url));
                            m.then(function(data){

                                data.data.forEach( function(element, index) {
                                var m= element.metric.file_system;
                                
                                if(m.startsWith("/dev")){
                                  $scope.kam_disk = [];
                                  element.values.forEach( function(value, index) {
                                      var timestamp = $rootScope.FixTimestamp(value[0]);
                                      $scope.kam_disk.push([timestamp,parseFloat(value[1])]);
                                  });

                                }
                              
                              });                
            
                      $scope.g_charts.push(Highcharts.stockChart('disk_chart_new', {
                              chart: {
                                  zoomType: 'x',
                              },
                              rangeSelector: {
                                  enabled: false
                              },
                              navigator: {
                                  enabled: false
                              },
                              title: {
                                  text: 'Disk usage over time'
                              },
                              subtitle: {
                                  text: document.ontouchstart === undefined ?
                                          'Click and drag in the plot area to zoom in' : 'Pinch the chart to zoom in'
                              },
                              xAxis: {
                                  type: 'datetime'
                              },
                              yAxis: {
                                  title: {
                                      text: 'Disk Usage %'
                                  }
                              },
                              legend: {
                                  enabled: false
                              },
                              credits: {
                                enabled: false
                              },
                              plotOptions: {
                                  area: {
                                      fillColor: {
                                          linearGradient: {
                                              x1: 0,
                                              y1: 0,
                                              x2: 0,
                                              y2: 1
                                          },
                                          stops: [
                                              [0, '#262B33'],
                                              [1, Highcharts.Color(Highcharts.getOptions().colors[0]).setOpacity(0).get('rgba')]
                                          ]
                                      },
                                      marker: {
                                          radius: 2
                                      },
                                      lineWidth: 1,
                                      states: {
                                          hover: {
                                              lineWidth: 1
                                          }
                                      },
                                      threshold: null
                                  }
                              },

                              series:[{
                                  type: 'area', color: '#454e5d',
                                  name: 'Disk',
                                  data: $scope.kam_disk
                              }]
                          }));
                    });
              }
            });          
          });
}





    
   $scope.getContainers = function(){

                            var end = $scope.current_time.toISOString();
                            var start = $scope.ten_m_before.toISOString();
                            var name = "cnt_created";
                            var step = "20m";

                            var url = $rootScope.apis.monitoring_data+
                                      "?end="+end+
                                      "&start="+start+
                                      "&name="+name+
                                      "&step="+step+
                                      "&labels[][labelid]=containers"+
                                      "&labels[][labeltag]=exported_job"+
                                      "&labels[][labelid]="+$scope.vm.exported_instance+
                                      "&labels[][labeltag]=exported_instance";

                            var m = Monitoring.getData(encodeURI(url));
                            m.then(function(data){
 
                                $scope.containers = []; 
                                
                                data.data.forEach(function(container,index){
                                
                                  var container = container;
                                  var ttime = container.values[0][1];
                                    
                                    container.created_date = $rootScope.FixTimestamp(ttime);
                                    container.status = 'Active'; 
                                    $scope.containers.push(container);
                                })
                             });

    }


    $scope.init = function(){
      (function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
      
      $scope.g_charts = [];

      $('.hchart').each(function(c){$(this).empty();});
      $('.highcharts-container').each(function(c){$(this).empty();});
      $scope.getVM();
      $scope.drawGauges();
      $scope.drawGaugesRAM();      
      $scope.historyCPU();
      $scope.historyRAM();
      $scope.historyHardDisk();
      $scope.getContainers();       
      $scope.loadCustomBoxes();   	
    }

      $scope.$on("$destroy", function(){
        $('.hchart').each(function(c){$(this).empty();});
        $('.highcharts-container').each(function(c){$(this).empty();});
        $scope.g_charts.forEach(function(chart){
          chart = null;
        });
        $scope.g_charts = null;
        $scope.intervals.forEach(function(interval){
          console.log("Clear Interval "+interval);
          $interval.cancel(interval);
        })
      });

     
    
}]);