provider "aws" {
	region = "${var.region}"
	access_key = "${var.access_key_var}"
	secret_key = "${var.secret_key_var}"
}

