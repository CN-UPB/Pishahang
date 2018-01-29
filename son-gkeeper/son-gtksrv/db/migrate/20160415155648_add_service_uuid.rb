class AddServiceUuid < ActiveRecord::Migration[4.2]
  def change
    add_column :requests, :service_uuid, :uuid
  end
end
