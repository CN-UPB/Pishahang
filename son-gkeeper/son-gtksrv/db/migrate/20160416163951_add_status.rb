class AddStatus < ActiveRecord::Migration[4.2]
  def change
    add_column :requests, :status, :string, :default => 'new'
  end
end
