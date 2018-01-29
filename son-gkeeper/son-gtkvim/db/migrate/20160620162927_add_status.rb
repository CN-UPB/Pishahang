class AddStatus < ActiveRecord::Migration
  def change
    add_column :vims_requests, :status, :string, :default => 'waiting'
  end
end
