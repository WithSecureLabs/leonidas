variable "aws_region" {
  description = "The AWS region to deploy into (default: us-west-2)."
  default     = "us-west-2"
}

variable "repo_default_branch" {
  description = "The name of the default repository branch (default: master)"
  default     = "master"
}

variable "environment" {
  description = "The environment being deployed (default: dev)"
  default     = "dev"
}

variable "build_timeout" {
  description = "The time to wait for a CodeBuild to complete before timing out in minutes (default: 5)"
  default     = "5"
}

variable "build_compute_type" {
  description = "The build instance type for CodeBuild (default: BUILD_GENERAL1_SMALL)"
  default     = "BUILD_GENERAL1_SMALL"
}

variable "build_image" {
  description = "The build image for CodeBuild to use (default: aws/codebuild/standard:2.0)"
  default     = "aws/codebuild/standard:2.0"
}

variable "package_buildspec" {
  description = "The buildspec to be used for the Package stage (default: buildspec.yml)"
  default     = "buildspec.yml"
}

variable "codecommit_ssh_key" {
  description = "SSH key for codecommit user"
  default = "~/.ssh/id_rsa.pub"
}
