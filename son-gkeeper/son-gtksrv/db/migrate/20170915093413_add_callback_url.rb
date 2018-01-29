class AddCallbackUrl < ActiveRecord::Migration[4.2]
  def change
    add_column :requests, :callback, :string
  end
  def down
    remove_column :requests, :callback
  end
end
