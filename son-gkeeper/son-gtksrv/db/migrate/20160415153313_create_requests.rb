class CreateRequests < ActiveRecord::Migration[4.2]
  def change
    create_table :requests, id: :uuid  do |t|
      t.timestamps
     end
  end
end
