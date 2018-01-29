## Copyright (c) 2015 SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
## ALL RIGHTS RESERVED.
## 
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
## 
##     http://www.apache.org/licenses/LICENSE-2.0
## 
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
## 
## Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
## nor the names of its contributors may be used to endorse or promote 
## products derived from this software without specific prior written 
## permission.
## 
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through 
## the Horizon 2020 and 5G-PPP programmes. The authors would like to 
## acknowledge the contributions of their colleagues of the SONATA 
## partner consortium (www.sonata-nfv.eu).
require_relative '../spec_helper'

RSpec.describe Metric, type: :model do
  def app() GtkApi end
  
  let(:known_metric_name1) {'vm_cpu_perc'}
  let(:known_metric_name2) {'ram_util'}
  let(:known_metric) {{name: known_metric_name1}}
  let(:known_metrics_response) {{:metrics=>{:resultType=>"vector", :result=>[{:metric=>{:exported_instance=>"INT-SRV-3", :core=>"cpu", :group=>"development", :exported_job=>"vm", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"a44a4d56-9bf4-4e15-aef4-0e5a52d0aec2"}, :value=>[1497360728.608, "5.94"]}, {:metric=>{:exported_instance=>"vtc-vnf", :core=>"cpu1", :group=>"development", :exported_job=>"vnf", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"d467cc91-12d3-4d81-bf90-b71acabaad61"}, :value=>[1497360728.608, "0"]}, {:metric=>{:exported_instance=>"TEST-VNF", :core=>"cpu1", :group=>"development", :exported_job=>"vnf", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"a44a4d56-9bf4-4e15-aef4-0e5a52d0aec2"}, :value=>[1497360728.608, "8.08"]}, {:metric=>{:exported_instance=>"TEST-VNF", :core=>"cpu", :group=>"development", :exported_job=>"vnf", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"a44a4d56-9bf4-4e15-aef4-0e5a52d0aec2"}, :value=>[1497360728.608, "8.96"]}, {:metric=>{:exported_instance=>"INT-SRV-3", :core=>"cpu1", :group=>"development", :exported_job=>"vm", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"a44a4d56-9bf4-4e15-aef4-0e5a52d0aec2"}, :value=>[1497360728.608, "6.93"]}, {:metric=>{:exported_instance=>"INT-SRV-3", :core=>"cpu0", :group=>"development", :exported_job=>"vm", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"a44a4d56-9bf4-4e15-aef4-0e5a52d0aec2"}, :value=>[1497360728.608, "5.88"]}, {:metric=>{:exported_instance=>"vtc-vnf", :core=>"cpu0", :group=>"development", :exported_job=>"vnf", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"d467cc91-12d3-4d81-bf90-b71acabaad61"}, :value=>[1497360728.608, "0"]}, {:metric=>{:exported_instance=>"vtc-vnf", :core=>"cpu", :group=>"development", :exported_job=>"vnf", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"d467cc91-12d3-4d81-bf90-b71acabaad61"}, :value=>[1497360728.608, "0"]}, {:metric=>{:exported_instance=>"TEST-VNF", :core=>"cpu0", :group=>"development", :exported_job=>"vnf", :instance=>"pushgateway:9091", :job=>"sonata", :__name__=>"vm_cpu_perc", :id=>"a44a4d56-9bf4-4e15-aef4-0e5a52d0aec2"}, :value=>[1497360728.608, "9.8"]}]}}}
  let(:unknown_metric_name1) {'abcd'}
  let(:unknown_metric_name2) {'efgh'}
  let(:metrics_url) {Metric.class_variable_get(:@@url)+'/prometheus/metrics/name' }
  let(:ok_response) {{status: 200, count: 1, items: [known_metric], message: 'OK'}}
  let(:not_found_response) {{status: 404, count: 0, items: [], message: 'Not Found'}}

  describe '#config' do
  end
  describe '#initialize' do
  end
  describe '#find' do
  end
  describe '#find_by_name' do
    context 'with a known metric name' do
      before(:each) do
        resp = OpenStruct.new(header_str: "HTTP/1.1 200 OK\nRecord-Count: 1", body: known_metrics_response.to_json)      
        allow(Curl).to receive(:get).with(metrics_url+'/'+known_metric_name1+'/').and_return(resp) 
      end
      it 'should return a Metric instance' do
        expect(Metric.find_by_name(known_metric_name1)).to be_a Metric
      end
      it 'should do a GET' do
        metric = Metric.find_by_name(known_metric_name1)
        expect(Curl).to have_received(:get)
      end
    end
    context 'with metric name that is' do
      it 'nil, should raise a MetricNameCanNotBeNilOrEmptyError exception' do
        expect{Metric.find_by_name(nil)}.to raise_error(MetricNameCanNotBeNilOrEmptyError)
      end
      it 'empty, should raise a MetricNameCanNotBeNilOrEmptyError exception' do
        expect{Metric.find_by_name('')}.to raise_error(MetricNameCanNotBeNilOrEmptyError)
      end
      it 'unknown, should raise a MetricNameNotFoundError exception' do
        resp = OpenStruct.new(header_str: "HTTP/1.1 404 OK\nRecord-Count: 0", body: not_found_response)
        allow(Curl).to receive(:get).with(metrics_url+'/'+unknown_metric_name1+'/').and_return(resp) 
        expect{Metric.find_by_name(unknown_metric_name1)}.to raise_error(MetricNameNotFoundError)
      end
    end
  end
  describe '.asynch_monitoring_data' do
    # AsynchMonitoringDataRequestNotCreatedError
  end
  describe '.synch_monitoring_data' do
    # SynchMonitoringDataRequestNotCreatedError
  end
  describe '#validate_and_create' do
    context 'should return' do
      let(:spied_metric) {spy('metric', name: known_metric_name1)}
      let(:spied_metric2) {spy('metric', name: known_metric_name2)}
      it 'an empty array when no metric names are passed' do
        expect(Metric.validate_and_create([])).to eq([])
      end
      it 'an empty array when only unknown metric names are passed' do
        resp = OpenStruct.new(header_str: "HTTP/1.1 404 OK\nRecord-Count: 0", body: '')      
        allow(Curl).to receive(:get).and_return(resp).twice
        expect(Metric.validate_and_create([unknown_metric_name1, unknown_metric_name2])).to eq([])
      end
      it 'a single element array when one known and one unknown metric names are passed' do    
        allow(Metric).to receive(:find_by_name).with(known_metric_name1).and_return(spied_metric)
        allow(Metric).to receive(:find_by_name).with(unknown_metric_name1).and_raise(MetricNameNotFoundError)
        expect(Metric.validate_and_create([known_metric_name1, unknown_metric_name1])).to eq([spied_metric])
      end
      it 'a double element array when both metric names passed are known' do    
        allow(Metric).to receive(:find_by_name).with(known_metric_name1).and_return(spied_metric)
        allow(Metric).to receive(:find_by_name).with(known_metric_name2).and_return(spied_metric2)
        expect(Metric.validate_and_create([known_metric_name1, known_metric_name2])).to eq([spied_metric, spied_metric2])
      end
    end
  end
end