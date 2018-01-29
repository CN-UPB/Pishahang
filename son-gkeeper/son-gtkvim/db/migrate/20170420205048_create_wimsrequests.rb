class CreateWimsrequests < ActiveRecord::Migration
  def change
    create_table :wims_requests, id: :uuid  do |t|
      t.timestamps
     end
  end
end
