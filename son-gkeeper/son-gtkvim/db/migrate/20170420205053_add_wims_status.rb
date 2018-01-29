class AddWimsStatus < ActiveRecord::Migration
  def change
    add_column :wims_requests, :status, :string, :default => 'waiting'
  end
end
