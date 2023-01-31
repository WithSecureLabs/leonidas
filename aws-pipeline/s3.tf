resource "aws_s3_bucket" "codebuild_bucket" {
  bucket_prefix = "leonidas-codebuild"
  force_destroy = true
}
