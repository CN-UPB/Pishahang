variable "ami_instance_id"{
	type = "string"
	default = "ami-0ef50ac7ce95adb40"
}

variable "access_key_var"{
	type = "string"
	default = ""
}

variable "secret_key_var"{
	type = "string"
	default = ""
}

variable "instance_name"{
	type = "string"
	default = "fpga_service"
}
variable "instance_type"{
	type = "string"
	default = "t2.micro"
}
variable "region"{
	type = "string"
	default = "eu-central-1"
}
