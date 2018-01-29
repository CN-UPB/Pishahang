require 'gtk/rate_limiter'
require 'gtk/limit'
require 'gtk/redis_store'
require 'gtk/store_error'
require 'gtk/config'

require 'sinatra/logger'

module Gtk

  Config.redis_url = ENV["REDIS_URL"] || 'redis://127.0.0.1:6379'

  # If you do not want to use password, do not set this environment variable. If you run redis in protected mode,
  # you must disable protected mode sending the command 'CONFIG SET protected-mode no' from the loopback interface
  # by connecting to Redis from the same host the server is running

  # If you set this env variable, the password must be set on the configuration file. Edit your redis.conf file, find
  # this line "# requirepass foobared", and change foobared to the value of the env variable.
  Config.redis_password = ENV["REDIS_PASSWORD"]


  class RateLimiter < Sinatra::Base

  end

end


