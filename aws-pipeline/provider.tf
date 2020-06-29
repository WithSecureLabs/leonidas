provider "aws" {
  version = "~> 2.0"
  region  = "us-east-1"
  profile = "default"
}

terraform {
  backend "s3" {
    bucket = "leonidas-tf-backend"
    key    = "tfstate/dev"
    region = "us-east-1"
    profile = "default"
  }
}
