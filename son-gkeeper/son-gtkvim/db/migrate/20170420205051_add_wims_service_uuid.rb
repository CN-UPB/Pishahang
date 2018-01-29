class AddWimsServiceUuid < ActiveRecord::Migration
  def change
    add_column :wims_requests, :query_uuid, :uuid
  end
end
