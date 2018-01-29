class AddServiceUuid < ActiveRecord::Migration
  def change
    add_column :vims_requests, :query_uuid, :uuid
  end
end
