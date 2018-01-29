class AddWimsQueryResponse < ActiveRecord::Migration
  def change
    add_column :wims_requests, :query_response, :json
  end
end
