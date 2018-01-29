##
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
# encoding: utf-8
require "SONATA/version"
require 'curb'
require 'json'

module SONATA
  class CurbAdapter
    def self.config(url:, logger:)
      raise ArgumentError.new('SONATA::CurbAdapter can not be configured with nil or empty url') if url.to_s.empty?
      raise ArgumentError.new('SONATA::CurbAdapter can not be configured with nil logger') if logger.nil?
      log_message = "SONATA::CurbAdapter#configure"
      @@url = url
      @@logger = logger
      @@logger.debug(log_message) {'entered with url='+url} if logger
      self
    end

    # This must be improved... it's silly to pass url: and logger: in every call!
    def self.find(url:, params: {}, headers: {}, logger:)
      log_message = "SONATA::CurbAdapter#find"
      logger.debug(log_message) {"entered: url=#{url}, params=#{params}, headers=#{headers}"}
      logger.debug(log_message) {"complete_url=#{complete_url(url, params)}"}
      begin
        res=Curl.get(complete_url(url, params)) do |req|
          if headers.empty?
            req.headers['Content-type'] = req.headers['Accept'] = 'application/json'
          else
            headers.each do |h|
              logger.debug(log_message) {"header[#{h[0]}]: #{h[1]}"}
              req.headers[h[0]] = h[1]
            end
          end
        end
        logger.debug(log_message) {"header_str=#{res.header_str}"}
        body = res.body
        logger.debug(log_message) {"response body=#{body}"}
        status = res.status.to_i
        case status
        when 200..299
          count = record_count_from_response_headers(res.header_str)
          begin
            parsed_response = body.empty? ? {} : JSON.parse(body, symbolize_names: true)
            logger.debug(log_message) {"parsed_response=#{parsed_response}"}
            if count == 0 && !parsed_response.to_s.empty?
              count = parsed_response.is_a?(Hash) ? 1 : parsed_response.count
            end
            {status: status, count: count, items: parsed_response.is_a?(Hash) ? [parsed_response] : parsed_response, message: "OK"}
          rescue => e
            logger.error(log_message) {"Error during processing: #{$!}"}
            logger.error(log_message) {"Backtrace:\n\t#{e.backtrace.join("\n\t")}"}
            {status: nil, count: nil, items: nil, message: "Error processing #{$!}: \n\t#{e.backtrace.join("\n\t")}"}
          end
        when 400
        when 404
          logger.debug(log_message) {"Records not found for url=#{url}, params=#{params}, headers=#{headers}"}
          {status: status, count: 0, items: [], message: "Not Found"}
        when 401
          logger.debug(log_message) {"Not authorized for url=#{url}, params=#{params}, headers=#{headers}"}
          {status: status, count: 0, items: [], message: "Unauthorized: missing authorization header"}
        else
          logger.debug(log_message) {"Unexpected status code received: #{status}"}
          {status: status, count: nil, items: nil, message: "Status #{status} unprocessable"}
        end
      rescue Curl::Err::ConnectionFailedError => e
        {status: 500, count: nil, items: nil, message: "Couldn't connect to server #{complete_url(url, params)}"}
      rescue Curl::Err::CurlError => e
        {status: 500, count: nil, items: nil, message: "Generic error while connecting to server #{complete_url(url, params)}"}
      rescue Curl::Err::AccessDeniedError => e
        {status: 500, count: nil, items: nil, message: "Access denied while connecting to server #{complete_url(url, params)}"}
      rescue Curl::Err::TimeoutError => e
        {status: 500, count: nil, items: nil, message: "Time out while connecting to server #{complete_url(url, params)}"}
      rescue Curl::Err::HostResolutionError => e
        {status: 500, count: nil, items: nil, message: "Couldn't resolve host name #{complete_url(url, params)}"}
      end
    end
  
    private
  
    def self.complete_url(url, params)
      params.empty? ? url : url + '?' + URI.encode_www_form(params)
    end
  
    def self.record_count_from_response_headers(header_str)
      # From http://stackoverflow.com/questions/14345805/get-response-headers-from-curb
      http_response, *http_headers = header_str.split(/[\r\n]+/).map(&:strip)
      http_headers = Hash[http_headers.flat_map{ |s| s.scan(/^(\S+): (.+)/) }]

      #http_response # => "HTTP/1.1 200 OK"
      #http_headers => { "Date" => "2013-01-10 09:07:42 -0700", "Content-Type" => "text/html", "Server" => "WEBrick/1.3.1 (Ruby/1.9.3/2012-11-10)",
      #        "Content-Length" => "62164", "Connection" => "Keep-Alive"}
      http_headers['Record-Count'].to_i
    end
  end
end
