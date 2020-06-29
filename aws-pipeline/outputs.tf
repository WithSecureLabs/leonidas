output "artifact_bucket" {
  value = "${aws_s3_bucket.codebuild_bucket}"
}

output "repo" {
  value = "${aws_codecommit_repository.repo}"
}

output "codecommit_iam_user" {
  value = "${aws_iam_user.codecommit_user}"
}

output "codecommit_iam_user_key" {
  value = "${aws_iam_user_ssh_key.codecommit_user_key}"
}

data "template_file" "ssh_config" {
  template = "${file("${path.module}/ssh_config.tpl")}"
  vars = {
    key_id = "${aws_iam_user_ssh_key.codecommit_user_key.id}"
    key = "${var.codecommit_ssh_key}"
  }
}

variable "ssh_config_template" {
  default = "ssh_config.tpl"
}


output "ssh_config" {
  value = "${templatefile(var.ssh_config_template, {key_id = aws_iam_user_ssh_key.codecommit_user_key.id, key = var.codecommit_ssh_key})}"
}
