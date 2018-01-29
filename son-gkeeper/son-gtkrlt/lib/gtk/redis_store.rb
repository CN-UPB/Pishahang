require_relative 'store_error'
require 'redis'

module Gtk
  class Store
    class << self
      LIMIT_PREFIX = "limit"

      def store_limit limit_hash
        begin
          redis.set("#{LIMIT_PREFIX}:#{limit_hash[:id]}", limit_hash.to_json)
        rescue Exception => e
          raise StoreError.new(e)
        end
      end

      def delete_limit limit_id
        begin
          redis.del("#{LIMIT_PREFIX}:#{limit_id}")
        rescue Exception => e
          raise StoreError.new(e)
        end
      end

      def find_limit limit_id
        begin
          raw_json = redis.get("#{LIMIT_PREFIX}:#{limit_id}")
          if raw_json
            JSON.parse(raw_json, :symbolize_names => true)
          else
            nil
          end
        rescue Exception => e
          raise StoreError.new(e)
        end
      end


      def find_all_limits
        begin
          limits = []
          redis.scan_each(:match => "#{LIMIT_PREFIX}:*") { |limit_key|
            limit_str = redis.get(limit_key)
            limits << JSON.parse(limit_str, :symbolize_names => true)
          }
          limits
        rescue Exception => e
          raise StoreError.new(e)
        end
      end

      def check_request_rate_limiter(bucket_id, leak_rate, capacity, requested_quantity)

        prefix = 'request_rate_limiter.' + bucket_id
        keys = [prefix + '.tokens', prefix + '.timestamp']

        # The arguments to the LUA script. time() returns unixtime in seconds.
        args = [leak_rate, capacity, Time.new.to_i, requested_quantity]

        begin
          recover_from_script_flush do
            allowed, tokens_left = redis.evalsha @overflow_script_sha, keys: keys, argv: args
            [allowed == "true", tokens_left]
          end
        rescue Exception => e
          raise StoreError.new(e)
        end
      end

      def flush
        redis.flushall
      end


      private
      def redis
        @redis ||= connect_redis_and_load_script
      end

      def connect_redis_and_load_script
        redis = Redis.new(:url => Config.redis_url, :password => Config.redis_password)
        @overflow_script_sha = redis.script(:load, OVERFLOW_SCRIPT)
        redis
      end

      def recover_from_script_flush
        retry_on_noscript = true
        begin
          yield
        rescue Redis::CommandError => e
          # When somebody has flushed the Redis instance's script cache, we might
          # want to reload our scripts. Only attempt this once, though, to avoid
          # going into an infinite loop.
          if retry_on_noscript && e.message.include?('NOSCRIPT')
            load_scripts
            retry_on_noscript = false
          else
            raise
          end
        end
      end

      #Redis scripts execute atomically. No other operations can run between fetching the count and writing the new count.
      OVERFLOW_SCRIPT = <<-eos
          local tokens_key = KEYS[1]
          local timestamp_key = KEYS[2]

          local leak_rate = tonumber(ARGV[1])
          local bucket_capacity = tonumber(ARGV[2])
          local now = tonumber(ARGV[3])
          local requested = tonumber(ARGV[4])

          local last_seen_tokens_in_bucket = tonumber(redis.call("get", tokens_key))
          if last_seen_tokens_in_bucket == nil then
            last_seen_tokens_in_bucket = 0
          end

          local last_refreshed = tonumber(redis.call("get", timestamp_key))
          if last_refreshed == nil then
            last_refreshed = 0
          end

          local elapsed_time_since_last_refresh  = math.max(0, now-last_refreshed)
          local expired_tokens_since_last_refresh = math.min(last_seen_tokens_in_bucket, elapsed_time_since_last_refresh * leak_rate)

          local tokens_in_bucket = last_seen_tokens_in_bucket - expired_tokens_since_last_refresh

          local allowed = tokens_in_bucket + requested <= bucket_capacity
      

          if allowed then
            tokens_in_bucket = tokens_in_bucket + requested

            -- We want our bucket to expire if idle a time span larger then period (ex. 2* period).
            --  leak_rate = bucket_capacity / period <=> period = bucket_capacity / leak_rate 
            local ttl =  math.floor(bucket_capacity / leak_rate) * 2
            redis.call("setex", tokens_key, ttl, tokens_in_bucket)
            redis.call("setex", timestamp_key, ttl, now)
          end

          -- We use  math.max (x,y) because bucket capacity may be redefined.
          return { tostring(allowed), math.max(0, bucket_capacity  - tokens_in_bucket) }
      eos
    end
  end
end
