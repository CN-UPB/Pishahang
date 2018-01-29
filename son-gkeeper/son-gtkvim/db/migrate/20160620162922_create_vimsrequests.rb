class CreateVimsrequests < ActiveRecord::Migration
  def change
    create_table :vims_requests, id: :uuid  do |t|
      t.timestamps
     end
  end
end
