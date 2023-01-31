provider "aws" {
  region  = "us-east-1"
}

terraform {
  backend "s3" {
    bucket = "wsec-leo-stg-tfstate"
    key    = "tfstate/dev"
    region = "us-east-1"
  }
}
