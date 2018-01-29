class AddBeganAtTime < ActiveRecord::Migration[4.2]
  def change
    add_column :requests, :began_at, :datetime
    remove_column :requests, :ingress
    remove_column :requests, :egress
  end
  def down
    add_column :requests, :ingress, :string
    add_column :requests, :egress, :string
    remove_column :requests, :began_at
  end
end
