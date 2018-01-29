module Gtk
  class Config

    class << self

      attr_accessor :redis_url, :redis_password

      def redis_url
        @redis_url || 'redis://127.0.0.1:6379'
      end

    end

  end
end