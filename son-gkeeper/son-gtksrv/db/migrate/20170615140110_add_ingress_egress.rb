class AddIngressEgress < ActiveRecord::Migration[4.2]
  def change
    add_column :requests, :ingress, :string
    add_column :requests, :egress, :string
  end
end
