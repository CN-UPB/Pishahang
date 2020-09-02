resource "aws_instance" "fpga" {
	ami           = "${var.ami_instance_id}"
	instance_type = "${var.instance_type}"

	tags = {
		Name = "${var.instance_name}"
	}
}

output "ids" {
  description = "List of IDs of instances"
  value       = "${aws_instance.fpga.*.id}"
}

output "arn" {
  description = "List of ARNs of instances"
  value       = "${aws_instance.fpga.*.arn}"
}

output "availability_zone" {
  description = "List of availability zones of instances"
  value       = "${aws_instance.fpga.*.availability_zone}"
}

output "placement_group" {
  description = "List of placement groups of instances"
  value       = "${aws_instance.fpga.*.placement_group}"
}

output "key_name" {
  description = "List of key names of instances"
  value       = "${aws_instance.fpga.*.key_name}"
}

output "password_data" {
  description = "List of Base-64 encoded encrypted password data for the instance"
  value       = "${aws_instance.fpga.*.password_data}"
}


output "public_ip" {
  description = "List of public IP addresses assigned to the instances, if applicable"
  value       = "${aws_instance.fpga.*.public_ip}"
}

output "ipv6_addresses" {
  description = "List of assigned IPv6 addresses of instances"
  value       = "${aws_instance.fpga.*.ipv6_addresses}"
}

output "primary_network_interface_id" {
  description = "List of IDs of the primary network interface of instances"
  value       = "${aws_instance.fpga.*.primary_network_interface_id}"
}

output "private_ip" {
  description = "List of private IP addresses assigned to the instances"
  value       = "${aws_instance.fpga.*.private_ip}"
}

output "security_groups" {
  description = "List of associated security groups of instances"
  value       = "${aws_instance.fpga.*.security_groups}"
}

output "vpc_security_group_ids" {
  description = "List of associated security groups of instances, if running in non-default VPC"
  value       = "${aws_instance.fpga.*.vpc_security_group_ids}"
}

output "subnet_id" {
  description = "List of IDs of VPC subnets of instances"
  value       = "${aws_instance.fpga.*.subnet_id}"
}

output "credit_specification" {
  description = "List of credit specification of instances"
  value       = "${aws_instance.fpga.*.credit_specification}"
}

output "instance_state" {
  description = "List of instance states of instances"
  value       = "${aws_instance.fpga.*.instance_state}"
}

output "root_block_device_volume_ids" {
  description = "List of volume IDs of root block devices of instances"
  value       = [for device in aws_instance.fpga.*.root_block_device : device.*.volume_id]
}

output "ebs_block_device_volume_ids" {
  description = "List of volume IDs of EBS block devices of instances"
  value       = [for device in aws_instance.fpga.*.ebs_block_device : device.*.volume_id]
}

output "tags" {
  description = "List of tags of instances"
  value       = "${aws_instance.fpga.*.tags}"
}

output "volume_tags" {
  description = "List of tags of volumes of instances"
  value       = "${aws_instance.fpga.*.volume_tags}"
}
