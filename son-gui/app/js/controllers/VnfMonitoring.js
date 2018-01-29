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

SonataApp.controller('VnfMonitoring',['$rootScope','$scope','$routeParams','$location','$http','$interval','Monitoring',function($rootScope,$scope, $routeParams, $location, $http,$interval,Monitoring){
  
  $scope.vnf = {};
  $scope.a_metrics = [];
  $scope.pagecharts = [];
  $scope.vnf.currentMemoryUsage = 0;
  $scope.vnf.currentCPUUsage = 0;
  $scope.view_details = false;
  $scope.btn_details_view = false;
  $scope.current_time = new Date();
  $scope.ten_m_before = new Date($scope.current_time.getTime() - 15*60000);
  $scope.settings_modal = {};
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

  
  $scope.potential_graphs = [];

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
  //console.log("Save Box Configuration Thing");
  $scope.addNewChart($scope.selected_box);
}

$scope.addNewChart = function(new_chart){

  //Local Storage Feauture
  $scope.custom_boxes.push(new_chart);
  $scope.custom_boxes.forEach(function(e,i){
    $scope.custom_boxes[i] = JSON.stringify($scope.custom_boxes[i]);
  });
  $rootScope.setStorage('sonata_custom_charts_vnf_'+$routeParams.name,JSON.stringify($scope.custom_boxes));
  $scope.loadCustomBoxes();
  //End Local Storage Feaute
}  


$scope.loadCustomBoxes = function(){
      console.log("Load Custom Boxes");
      $scope.custom_boxes = [];
      $scope.custom_boxes = $rootScope.getStorage('sonata_custom_charts_vnf_'+$routeParams.name);
      $scope.custom_boxes = JSON.parse($scope.custom_boxes);
      //console.log($scope.custom_boxes);
      
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
  console.log("appearCustomCharts");
  $scope.custom_boxes.forEach(function(e,i){
    $scope.fillnewBox(e);
  })
}

$scope.configureBox = function(box){
  $scope.selected_box = box;
  $('#settings_modal').openModal();
}

$scope.updateBox = function(box){
  $scope.fillnewBox(box);
}
$scope.removeBox = function(box){

  for (var i =0; i < $scope.boxes.length; i++){
    
    if($scope.boxes[i].id === box.id) {
      $scope.boxes.splice(i,1);
      break;
   }
  }
   for (var i =0; i < $scope.custom_boxes.length; i++){
    
    if ($scope.custom_boxes[i].id === box.id) {
      $scope.custom_boxes.splice(i,1);
      $scope.custom_boxes.forEach(function(e,i){
        $scope.custom_boxes[i] = JSON.stringify($scope.custom_boxes[i]);
      });
      $rootScope.setStorage('sonata_custom_charts_vnf_'+$routeParams.name,JSON.stringify($scope.custom_boxes));
      $scope.loadCustomBoxes();
   }
   }
   

}


 $scope.getRecords = function(){
      

                var m = Monitoring.getRecords();
                m.then(function(data){
                  console.log("getRecord");
                  //console.log(data);

                  data.data.forEach(function(r,i){
                    // console.log("Record");
                    // console.log(r);
                    var this_i = i;

                    r.virtual_deployment_units.forEach(function(vdu,x){
                     
                      vdu.vnfc_instance.forEach(function(vnfc,y){
                        if(vnfc.vc_id==$routeParams.name){
                          $scope.btn_details_view = true;
                         
                          $scope.connection_points = vnfc.connection_points;
                          $scope.getDescriptor(r.descriptor_reference);
                          // console.log("virtual_deployment_units:"+i);
                          // console.log(r.virtual_deployment_units);
                          console.log(this_i);
                          console.log(vnfc.vc_id);
                          console.log("virtual_deployment_units");
                          console.log(r.virtual_deployment_units);
                          angular.forEach(r.virtual_deployment_units,function(d){
                            angular.forEach(d.monitoring_parameters,function(mp){
                              $scope.potential_graphs.push(mp);
                            });
                          });
                        }
                      })
                    })
                  })
                  if($scope.potential_graphs.length==0){
                            $scope.addAlternativeParameters();
                  }
                });
    }
    $scope.getRecords();

    $scope.getDescriptor = function(descriptor_reference){
      $scope.descriptor = {}
      $scope.descriptor.vnfd = {};
      $scope.descriptor.vnfd.monitoring_rules = [];
      $scope.descriptor.vnfd.monitoring_rules.push({"description":"Trigger events if CPU load is above 10 percent.","duration":"10","duration_unit":"s","condition":"vdu01:vm_cpu_perc > 10"});
      $scope.descriptor.vnfd.monitoring_rules.push({"description":"Trigger events if CPU load is above 10 percent.","duration":"10","duration_unit":"s","condition":"vdu01:vm_cpu_perc > 10"});

            $http({
                method  : 'GET',
                url     : $scope.apis.gatekeeper.functions,
                headers : $rootScope.getGKHeaders()
               })
                .success(function(data) {
                  angular.forEach(data,function(d){
                      if(descriptor_reference==d.uuid){
                        $scope.descriptor = d;
                      }
                  });

                })
                .error(function(data){
                  console.error('Get functions Failed. Get Url: '+$scope.apis.gatekeeper.functions);
                  console.error(data);
                })
    }
    $scope.toggleDetails = function(){
      $scope.view_details = !$scope.view_details;
    }
    $scope.addAlternativeParameters = function(){
  
        $http({
                method  : 'GET',
                url     : $scope.apis.monitoring_list,
                headers : { 'Content-Type': 'application/json' }
               })
                .success(function(data) {
                  data.metrics.forEach(function(metric,index){
                    if(metric.startsWith('vm_')){
                      var x = {};
                      x.name = metric;
                      
                      $scope.potential_graphs.push(x);
                    }

                      
                  })
                 
                  
                });
}


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
        m.then(function(datas){
          
                    $scope.data = [];
                    if(datas.data[0]){
                     datas.data[0].values.forEach(function(element, index) {

                            var timestamp = $rootScope.FixTimestamp(element[0]);
                            $scope.data.push([timestamp,parseFloat(element[1])]);
                         
                       });


                     console.log("I will check");
                     if($scope.data.length>0){
                      console.log("NAI EXW:"+$scope.data);
                      console.log($scope.data);
                      $scope.g_charts.push(Highcharts.stockChart(box.id, {
                              chart: {
                                  zoomType: 'x'
                              },
                              animation:false,
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
                                  type: 'line',
                                  color: '#454e5d',
                                  name: box.measurement,
                                  data: $scope.data
                              }]
                          }));
                     }else{
                      
                      $('#'+box.id).html('No data available');
                     }

                    }else{
                      
                      $('#'+box.id).html('No data available for '+box.measurement);
                     
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


$scope.addPoints = function () {
      var seriesArray = $scope.chartConfig.series
      var rndIdx = Math.floor(Math.random() * seriesArray.length);
      seriesArray[rndIdx].data = seriesArray[rndIdx].data.concat([1, 10, 20])
    };

    var series = 0;
    $scope.addSeries = function () {
      var rnd = []
      for (var i = 0; i < 10; i++) {
        rnd.push(Math.floor(Math.random() * 20) + 1)
      }
      $scope.chartConfig.series.push({
        data: rnd,
        id: 'series_' + series++
      })
    }

    $scope.removeRandomSeries = function () {
      var seriesArray = $scope.chartConfig.series
      var rndIdx = Math.floor(Math.random() * seriesArray.length);
      seriesArray.splice(rndIdx, 1)
    }

    $scope.swapChartType = function () {
      this.chartConfig.chart.polar = !this.chartConfig.chart.polar;

    }

    

$scope.getVM = function(){
        var start = new Date(new Date().getTime() - 20*60000).toISOString()
        var end   = new Date().toISOString();
        var name  = 'vm_mem_perc';
        var step  = "10m";

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]=vnf"+
                  "&labels[][labeltag]=exported_job"+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){

           $scope.vnf.exported_instance = data.data[0].metric.exported_instance;
           $scope.vnf.instance          = data.data[0].metric.instance;
           $scope.vnf.group             = data.data[0].metric.group;
           $scope.vnf.id                = data.data[0].metric.id;
            
          });
}




$scope.drawGaugesRAM = function(){
   google.charts.setOnLoadCallback(drawChart);
      function drawChart() {

        var data = google.visualization.arrayToDataTable([
          ['Label', 'Value'],
          ['Memory', parseFloat($scope.vnf.currentMemoryUsage)],
        ]);

        var options = {
          width: 400, height: 120,
          redFrom: 90, redTo: 100,
          yellowFrom:75, yellowTo: 90,
          minorTicks: 5
        };

        var chart = new google.visualization.Gauge(document.getElementById('vRAMschart'));
        chart.draw(data, options);
      }
}

$scope.drawGauges = function(){
   google.charts.setOnLoadCallback(drawChart);
      function drawChart() {

        var data = google.visualization.arrayToDataTable([
          ['Label', 'Value'],          
          ['CPU', parseFloat($scope.vnf.currentCPUUsage)]
        ]);

        var options = {
          width: 400, height: 120,
          redFrom: 90, redTo: 100,
          yellowFrom:75, yellowTo: 90,
          minorTicks: 5
        };

        var chart = new google.visualization.Gauge(document.getElementById('vCPUschart'));

        chart.draw(data, options);

       
      }
}

$scope.drawTheChart = function(data_array,options,element){

       var data = google.visualization.arrayToDataTable(data_array);
       var options = options;
       var chart = new google.visualization.AreaChart(document.getElementById(element));
       chart.draw(data, options);
       

}


$scope.historyRAM = function(){


        var start = new Date(new Date().getTime() - 20*60000).toISOString();
        var end   = new Date().toISOString();
        var name  = "vm_mem_perc";
        var step  = "10s";

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]=vnf"+
                  "&labels[][labeltag]=exported_job"+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(datas){

          $scope.ramdata = [];
          $scope.vnf.currentMemoryUsage = 100-datas.data[0].values[datas.data[0].values.length-1][1];
           datas.data[0].values.forEach(function(element, index) {

                  var timestamp = $rootScope.FixTimestamp(element[0]);
                  $scope.ramdata.push([timestamp,parseFloat(100-element[1])]);
                  

                if(index==datas.data[0].values.length-1){
                  
                  $scope.vnf.currentMemoryUsage = parseFloat(100-element[1]);
                  $scope.drawGauges();
                }

             });



                $scope.g_charts.push(Highcharts.stockChart('ram_chart_new_vnf', {
                              chart: {
                                zoomType: 'x',
                                animation:false,
                                  rangeSelector: {
                                    enabled: false
                                  },
                                  navigator: {
                                    enabled: false
                                  },
                                  animation:false,
                                  events: {
                                      load: function () {

                                          
                                          var series = this.series[0];
                                          $scope.intervals.push($interval(function () {

                                          var start = new Date().toISOString();
                                            var end   = new Date().toISOString();
                                            var name  = "vm_mem_perc";
                                            var step  = "10s";

                                            var url = $rootScope.apis.monitoring_data+
                                                      "?end="+end+
                                                      "&start="+start+
                                                      "&name="+name+
                                                      "&step="+step+
                                                      "&labels[][labelid]=vnf"+
                                                      "&labels[][labeltag]=exported_job"+
                                                      "&labels[][labelid]="+$routeParams.name+
                                                      "&labels[][labeltag]=id";

                                            var m = Monitoring.getData(encodeURI(url));
                                            m.then(function(data){
                                                    
                                                    var y = data.data[0].values[0][1];
                                                    var x = data.data[0].values[0][0];
                                                    var timestamp = $rootScope.FixTimestamp(x);
                                                      series.addPoint([timestamp, parseFloat(100-y)], true, true);
                                                      $scope.vnf.currentMemoryUsage = 100-y;
                                                      $scope.drawGaugesRAM();

                                                  })                                  





                                          }, 5000));
                                      


                                      }
                                    }
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
                              animation:false,
                                  rangeSelector: {
                                    enabled: false
                                  },
                                  navigator: {
                                    enabled: false
                                  },
                              legend: {
                                  enabled: false
                              },
                              credits: {
                                enabled: false
                              },
                              plotOptions: {
                                  area: {
                                      /*fillColor: {
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
                                      },*/
                                      marker: {
                                          radius: 1
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
                                  type: 'line',
                                  color: '#454e5d',
                                  name: 'RAM',
                                  data: $scope.ramdata
                              }]
                          }));
          });
}






$scope.historyCPU = function(){

 var start = new Date(new Date().getTime() - 20*60000).toISOString();
          var end   = new Date().toISOString();
          var name  = "vm_cpu_perc";
          var step  = "10s";

          var url = $rootScope.apis.monitoring_data+
                    "?end="+end+
                    "&start="+start+
                    "&name="+name+
                    "&step="+step+
                    "&labels[][labelid]=vnf"+
                    "&labels[][labeltag]=exported_job"+
                    "&labels[][labelid]="+$routeParams.name+
                    "&labels[][labeltag]=id";

          var m = Monitoring.getData(encodeURI(url));
          m.then(function(data){

            $scope.prdata = [];               
            $scope.vnf.currentCPUUsage = data.data[0].values[data.data[0].values.length-1][1];                    
            data.data[0].values.forEach(function(element, index) {

                  var timestamp = $rootScope.FixTimestamp(element[0]);
                  $scope.prdata.push([timestamp,parseFloat(element[1])]);
            

             });

                       $scope.g_charts.push(Highcharts.stockChart('cpu_chart_new_vnf', {
                              chart: {
                                  zoomType: 'x',
                                  animation:false,
                                  rangeSelector: {
                                    enabled: false
                                  },
                                  navigator: {
                                    enabled: false
                                  },
                                  events: {
                                      load: function () {

                                          
                                          var series = this.series[0];
                                          $scope.intervals.push($interval(function () {

                                          var start = new Date().toISOString();
                                          var end   = new Date().toISOString();
                                          var name  = "vm_cpu_perc";
                                          var step  = "10s";

                                          var url = $rootScope.apis.monitoring_data+
                                                    "?end="+end+
                                                    "&start="+start+
                                                    "&name="+name+
                                                    "&step="+step+
                                                    "&labels[][labelid]=vnf"+
                                                    "&labels[][labeltag]=exported_job"+
                                                    "&labels[][labelid]="+$routeParams.name+
                                                    "&labels[][labeltag]=id";

                                          var m = Monitoring.getData(encodeURI(url));
                                          m.then(function(data){
                                          
                                                    
                                                    var y = data.data[0].values[0][1];
                                                    var x = data.data[0].values[0][0];
                                                    var timestamp = $rootScope.FixTimestamp(x);                                                      
                                                      series.addPoint([timestamp, parseFloat(y)], true, true);
                                                      $scope.vnf.currentCPUUsage = parseFloat(y);
                                                      $scope.drawGauges();


                                                  })

                                          }, 5000));
                                      


                                      }
                                    }
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
                              animation:false,
                                  rangeSelector: {
                                    enabled: false
                                  },
                                  navigator: {
                                    enabled: false
                                  },
                              legend: {
                                  enabled: false
                              },
                              credits: {
                                enabled: false
                              },
                              series: [{
                                  type: 'line',
                                  color: '#454e5d',
                                  name: 'CPU',
                                  data: $scope.prdata
                              }]
                          }));










































































          });

}




















$scope.historyHardDisk = function(){




        var start = new Date(new Date().getTime() - 15*60000).toISOString();
        var end   = new Date().toISOString();
        var name  = "vm_disk_usage_perc";
        var step  = "1m";

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]=vnf"+
                  "&labels[][labeltag]=exported_job"+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){


            $scope.vnf.disk_total = 0;
            data.data.forEach( function(element, index) {
              var m= element.metric.file_system;
              if(m.startsWith("/dev")){

                $scope.vnf.disk_total = parseFloat(element.values[0][1]);

                var start = new Date(new Date().getTime() - 15*60000).toISOString();
                var end   = new Date().toISOString();
                var name  = "vm_disk_usage_perc";
                var step  = "1m";

                var url = $rootScope.apis.monitoring_data+
                          "?end="+end+
                          "&start="+start+
                          "&name="+name+
                          "&step="+step+
                          "&labels[][labelid]=vnf"+
                          "&labels[][labeltag]=exported_job"+
                          "&labels[][labelid]="+$routeParams.name+
                          "&labels[][labeltag]=id";

                var m = Monitoring.getData(encodeURI(url));
                m.then(function(data){
                    
                    data.data.forEach(function(element, index) {
                        var m= element.metric.file_system;
                        if(m.startsWith("/dev")){
                          $scope.kam_disk = [];
                          element.values.forEach( function(value, index) {

                              var timestamp = $rootScope.FixTimestamp(value[0]);
                              $scope.kam_disk.push([timestamp,parseFloat(value[1])]);
                          });

                        }
                      
                      });
                  

            



              $scope.g_charts.push(Highcharts.stockChart('disk_chart_new_vnf', {
                              chart: {
                                  zoomType: 'x',
                              },
                              rangeSelector: {
                                  enabled: false
                              },
                              navigator: {
                                  enabled: false
                              },
                              animation:false,
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
                              series:[{
                                  type: 'line', 
                                  color: '#454e5d',
                                  name: 'Disk',
                                  data: $scope.kam_disk
                              }]
                          }));


                   

                    });





              }

            });
          
          });





}
$scope.getCurrentCPU = function(){
  
        var start = new Date().toISOString();
        var end   = new Date().toISOString();
        var name  = "vm_cpu_perc";
        var step  = "1m";

        var url = $rootScope.apis.monitoring_data+
                  "?end="+end+
                  "&start="+start+
                  "&name="+name+
                  "&step="+step+
                  "&labels[][labelid]=vnf"+
                  "&labels[][labeltag]=exported_job"+
                  "&labels[][labelid]="+$routeParams.name+
                  "&labels[][labeltag]=id";

        var m = Monitoring.getData(encodeURI(url));
        m.then(function(data){

            $scope.vnf.currentCPUUsage = data.data[0].values[0][1];
            
          });
}




    $scope.getRecords = function(){
      
    

                var m = Monitoring.getRecords();
                m.then(function(data){
                  console.log("getRecord");
                  console.log(data);
                  data.data.forEach(function(r,i){
               
                    r.virtual_deployment_units.forEach(function(vdu,x){
                     
                      vdu.vnfc_instance.forEach(function(vnfc,y){
                        if(vnfc.vc_id==$routeParams.name){
                          console.log("Found R:"+i);
                          console.log("Found VDU:"+x);
                          console.log(r.virtual_deployment_units[i]);
                          console.log("I found it "+vnfc.vc_id);
                          console.log(vnfc);
                          $scope.connection_points = vnfc.connection_points;
                        }
                      })
                    })
                    
                    
                  })
                });
    }
    $scope.getRecords();
    
     $scope.getContainers = function(){
                var start = new Date(new Date().getTime() - 15*60000).toISOString();
                var end   = new Date().toISOString();
                var name  = "vm_disk_usage_perc";
                var step  = "1m";

                var url = $rootScope.apis.monitoring_data+
                          "?end="+end+
                          "&start="+start+
                          "&name="+name+
                          "&step="+step+
                          "&labels[][labelid]=containers"+
                          "&labels[][labeltag]=exported_job"+
                          "&labels[][labelid]="+$routeParams.name+
                          "&labels[][labeltag]=id";

                var m = Monitoring.getData(encodeURI(url));
                m.then(function(data){
                  $scope.containers = data.data;
                });
    }


    $scope.init = function(){
      (function(w){w = w || window; var i = w.setInterval(function(){},100000); while(i>=0) { w.clearInterval(i--); }})(/*window*/);
      $scope.g_charts = [];
      $scope.intervals = [];
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
          //chart.destroy();
          chart = null;
        });
        $scope.g_charts = [];
        $scope.intervals.forEach(function(interval){
          $interval.cancel(interval);
        });

         $scope.kam_disk.clear();
         $scope.prdata.clear();
         $scope.ramdata.clear();
         $scope.vnf.clear();
         $scope.data.clear();
      });
    
    
}]);