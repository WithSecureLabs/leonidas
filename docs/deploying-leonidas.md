# Deploying Leonidas

There are two supported options for deploying the Leonidas API:

* Deploying the CI/CD pipeline into AWS, then letting that generate and deploy the API
* Generating and running it locally

The former is recommended for producton, as it provides a stronger security model (such as the built-in API key authentication on the API gateway deployed as part of the API). The latter is best suited for development purposes.

## Deploying Leonidas to AWS

There are two parts to deploying Leonidas. First, the pipeline is created, then the API deployed.

### Deploying the Pipeline

The simplest and most reliable way to run the Leonidas API is via the CI/CD pipeline. This is deployed as follows:

* Install Terraform 0.12+ - (https://www.terraform.io/downloads.html)[https://www.terraform.io/downloads.html]
* `cd aws-pipeline`
* Modify `provider.tf`
  * Set the region you wish to deploy the pipeline into
  * Remove the `terraform` block if not using S3 remote state. If it is desired, configure for your own S3 bucket
  * Set the AWS CLI profile name to use in the `profile` fields
* Run `terraform plan` to ensure no syntax errors as a result of the above edit
* Run `terraform apply` to deploy the pipeline

### Building and Deploying the API

Once Leonidas is deployed, push the code up to the repository.

* `cd ./aws-pipeline`
* `terraform output repo`, take the `clone_url_ssh`
* `terraform output ssh_config`, take the `User`
* Merge the two outputs into a single URL, the final URL should be of the format `ssh://USER@git-codecommit....` where `USER@` is added just after the `ssh://` of the `clone_url_ssh`
* Add the new CodeCommit repository URL as a remote - `git remote add pipeline [URL]`
* Modify `generator/config.yml` to set the region into which you wish to deploy the API
* `git push pipeline master`
* Wait for the pipeline to deploy Leonidas, you can track this in the CodePipeline interface in the AWS GUI. It should only take a few minutes
* Get the rest API id by running `aws apigateway get-rest-apis | jq -r .items[].id`
* The URL will be `https://[API-ID].execute-api.[REGION].amazonaws.com/dev/`

To allow others to deploy updates and new test cases to this Leonidas instance, create an IAM user for each of them, add an SSH key to the IAM user, and add the user to the `codecommit_group` IAM group.

## Generating an IAM Policy for the API

The API is deployed with an appropriate role and policy for the test cases defined. Should you wish to deploy roles into other accounts for the Leonidas API to assume, it is possible to generate the JSON document needed to create a suitable IAM policy with the following command:

* `poetry run ./generator.py iam-policy`

## Removing Leonidas from an AWS account

* Install the serverless framework locally
* Change directory into `generator/`
* `poetry install`
* `serverless plugin install --name serverless-python-requirements`
* `serverless plugin install --name serverless-wsgi`
* `poetry run ./generator.py serverless-config > serverless.yml`
* `sls remove`
* Change directory into `aws-pipeline/`
* `terraform destroy`
* Check both the intended deployment region and us-east-1 for lingering S3 buckets, as the AWS API will not allow deletion of non-empty buckets. This can instead be done through the console.

## Running the Leonidas API Locally

It is possible to build and run the Leonidas AWS API locally for development purposes. To do this:

* `cd generator`
* `poetry install`
* `poetry run ./generator.py generate-aws-api`
* `cd ../output/leonidas`
* `poetry run python leonidas.py`

This will spawn the API listening at http://127.0.0.1:5000. By default, this uses whichever AWS credentials are configured as the default profile in `~/.aws/config`. This can be overridden by supplying a role ARN to assume, or access keys to use, as part of the requests to the API.
