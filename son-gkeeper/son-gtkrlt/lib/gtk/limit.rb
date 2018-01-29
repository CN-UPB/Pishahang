require 'json'

module Gtk
  class Limit
    attr :id
    attr_accessor :period, :limit, :description

    def initialize(params = {})
      @id = params[:id]
      @period = params[:period]
      @limit = params[:limit]
      @description = params[:description]
    end

    def upsert
      Store.store_limit({id: id, period: period, limit: limit, description: description})
    end

    def delete
      Store.delete_limit(id)
    end

    def self.find_by_id(id)
      json = Store.find_limit(id)
      if json
        Limit.new(json)
      else
        nil
      end
    end

    def self.find_all
      Store.find_all_limits
    end
    
    def bucket(client_id)
      Bucket.new("#{id}:#{client_id}", limit, period)
    end

    def to_json
      {id: id, period: period, limit: limit, description: description}.to_json
    end
  
    private
    class Bucket
      attr :id
      attr_accessor :capacity, :period
      def initialize bucket_id, limit, period
        @id = bucket_id
        @capacity = limit  #Max requests the bucket can hold

        @period = period
      end

      # Frequency that out bucket leaks requests (i.e how frequently requests expire)
      # 1 req / 10 sec => leak = 0.1 req/sec
      # 3600 req / 1 sec => leak = 3600 req/sec
      def leak_rate
        capacity.to_f / period
      end

      def request(quantity = 1)
        allowed, remaining = Store.check_request_rate_limiter(id, leak_rate, capacity, quantity)
      end
    end
  end

end
