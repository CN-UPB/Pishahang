class UpdateRequests < ActiveRecord::Migration[4.2]
  def up
    change_column_default :requests, :status, 'NEW'
    add_column :requests, :request_type, :string, :default => 'CREATE'
    add_column :requests, :service_instance_uuid, :uuid
  end
  def down
    change_column_default :requests, :status, 'new'
    remove_column :requests, :request_type
    remove_column :requests, :service_instance_uuid
  end
end
