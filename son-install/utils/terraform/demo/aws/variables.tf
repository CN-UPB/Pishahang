variable "aws_access_key" { default = "arocha@ptinovacao.pt" }
variable "aws_secret_key" { default = "" }
variable "aws_region" { default = "eu-west-1" }

variable "aws_public_key_path" { default = "~/.ssh/aws-arocha-keypair.pem" }
variable "aws_public_key_name" { default = "aws-arocha-keypair" }

variable "aws_amis" {
  default = {
    eu-west-1 = "ami-ac9ad1df"
    #eu-west-2 = ""
  }
}
