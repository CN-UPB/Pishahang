require 'sinatra/base'

module Gtk
  class RateLimiter < Sinatra::Base
    before do
      content_type :json
    end

    put "/limits/:limit_id" do
      begin
        body = request.body.read
        body_p = JSON.parse(body, :symbolize_names => true)

        respond(400, "must provide a positive int value for \"period\" field.") unless positive_int?(body_p[:period])
        respond(400, "must provide a positive int value for \"limit\" field.") unless positive_int?(body_p[:limit])

        limit = Limit.new(
          id: params[:limit_id],
          period: body_p[:period],
          limit: body_p[:limit],
          description: body_p[:description]
        )

        limit.upsert

        respond(201, "Limit was created or updated")

      rescue JSON::ParserError => e
        logger.error(e.backtrace.join("\n"))
        respond(400, "Unable to parse received message: #{e.message}")
      rescue StoreError => e
        logger.error(e.backtrace.join("\n"))
        respond(500, "Unable to create or update the limit. Caused by: #{e.message}")
      end
    end

    get "/limits/:limit_id" do
      begin
        limit = Limit.find_by_id(params[:limit_id])

        respond(404, "Limit with id \"#{params[:limit_id]}\" was not found") if limit.nil?
    
        halt 200, limit.to_json
      rescue StoreError => e
        logger.error(e.backtrace.join("\n"))
        respond(500, "Unable to delete limit. Caused by: #{e.message}")
      end
    end

    delete "/limits/:limit_id" do
      begin
        limit = Limit.find_by_id(params[:limit_id])

        respond(404, "Limit with id \"#{params[:limit_id]}\" was not found") if limit.nil?
    
        limit.delete
        respond(204, "Limit was deleted")
      rescue StoreError => e
        logger.error(e.backtrace.join("\n"))
        respond(500, "Unable to delete limit. Caused by: #{e.message}")
      end
    end


    get "/limits" do
      begin
        limits = Limit.find_all
        halt 200, limits.to_json
      rescue StoreError => e
        logger.error(e.backtrace.join("\n"))
        respond(500, "Unable to retrieve limits. Caused by: #{e.message}")
      end
    end
  
    post "/check" do
      begin
        body = request.body.read
        body_p = JSON.parse(body, :symbolize_names => true)

        limit_id = body_p[:limit_id].to_s
        client_id = body_p[:client_id].to_s
            

        respond(400, "\"limit_id\" cannot be null or an empty string.") if limit_id.empty?
        respond(400, "\"client_id\" cannot be null or an empty string.") if client_id.empty?

        limit = Limit.find_by_id(limit_id)
        respond(400, "Limit with id \"#{params[:limit_id]}\" was not found") if limit.nil?

        allow, remaining = limit.bucket(client_id).request(1)

        halt 200, { allowed: allow, remaining: remaining }.to_json

      rescue StoreError => e
        logger.error(e.backtrace.join("\n"))
        respond(500, "Unable to check limit. Caused by: #{e.message}")
      end
    end
  
    private
    def positive_int? value
      value.is_a?(Integer) && value > 0
    end

    def respond(status, message)
      logger.debug( "status: #{status} message: #{message}")
      halt status, {status: status, message: message}.to_json
    end
  end
end
