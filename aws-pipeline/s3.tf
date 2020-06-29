resource "aws_s3_bucket" "codebuild_bucket" {
  bucket_prefix = "leonidas-codebuild"
  acl           = "private"
  force_destroy = true
}
