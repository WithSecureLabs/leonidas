# Deploying Leonidas

There are two supported options for deploying the Leonidas API:

* Deploying the CI/CD pipeline into AWS, then letting that generate and deploy the API
* Generating and running it locally

The former is recommended for production, as it provides a stronger security model (such as the built-in API key authentication on the API gateway deployed as part of the API). The latter is best suited for development purposes.

## Deploying Leonidas to AWS

There are two parts to deploying Leonidas. First, the pipeline is created, then the API deployed.

### Deploying the Pipeline

The simplest and most reliable way to run the Leonidas API is via the CI/CD pipeline. This is deployed as follows:

* Install Terraform 0.12+ - [https://www.terraform.io/downloads.html](https://www.terraform.io/downloads.html)
* `cd aws-pipeline`
* Modify `provider.tf`
  * Set the region you wish to deploy the pipeline into
  * Remove the `terraform` block if not using S3 remote state. If it is desired, configure for your own S3 bucket
  * Set the AWS CLI profile name to use in the `profile` fields
* Run `terraform init` to instantiate the providers
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

### Generating an IAM Policy for the API

The API is deployed with an appropriate role and policy for the test cases defined. Should you wish to deploy roles into other accounts for the Leonidas API to assume, it is possible to generate the JSON document needed to create a suitable IAM policy with the following command:

* `poetry run ./generator.py iam-policy`

### Removing Leonidas from an AWS account

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

## Deploying Leonidas in a Kubernetes Cluster

Leonidas can be deployed as a containerised application within a pod in an existing Kubernetes cluster. On a high level, this includes generating the Python API from the definitions, packaging the code into a container image and pushing it to a repository, which can then be pulled into a Kubernetes pod as part of the Leonidas Kubernetes resources deployed within the cluster. All these steps can be carried out using the **generator** utility. 

It is recommended that **ephemeral images** are used for the Leonidas image. An example public repository supporting ephemeral images is [ttl.sh](ttl.sh), which is used in the commands below.

### Building and Deploying the API

The complete list of commands needed to deploy the Leonidas API within a cluster are provided below: 
0. Modify `config.yml`  to specify 
	- `image_url`: the image URL i.e. the registry to temporary push the Leonidas container image so that the cluster can pull it from. We recommend the use of *ephemeral images*, therefore the current default value uses the [ttl.sh](ttl.sh) registry with a few minutes image lifespan 
	 - `namespace`: the namespace which Leonidas resources should be deployed in. If not specified, Leonidas will be deployed into the `default` namespace. 
1. `cd generator/` - Navigate to the generator directory
2. `poetry install` - Install generator dependencies
3. `poetry run ./generator.py generate-kube-api` - To generate the Python API code from the YAML definitions
4. `poetry run ./generator.py build-image` - Build the Leonidas container image and push it to the remote registry. This might take a while.
5. `poetry run ./generator.py kube-resources > leonidas-manifests.yml`  - Create the manifest of Kubernetes resources Leonidas needs, including the RBAC policy
	- by default, this command assumes cluster-wide operation and generates a cluster role. To specify explicitly whether Leonidas should be granted namespaced or cluster-wide permissions, set the `--role/--clusterrole` flag 
6. `kubectl -f leonidas-manifests.yml apply` - Create the Leonidas resources in the cluster. This might take a minute.
7. `kubectl port-forward deployment/leonidas-deployment 5000:5000` - Expose the Flask web service on http://localhost:5000 so that it can be accessed by clients such as `leo`, Jupyter notebooks, or just `curl`. Note that if you chose to deploy Leonidas into a namespace other than the default, you will need to also provide the `-n <your-namespace>` flag here

### Removing Leonidas from a cluster
To clean up all Leonidas-related resources after use, simply run
`kubectl -f leonidas-manifests.yml delete`

### Generating an RBAC Policy for the API

The generator utility allows generation of only the RBAC policy needed by Leonidas, without the other Kubernetes resources. This can be done using the `rbac-policy` command. 

Leonidas can be configured to run with cluster-wide permissions, or limited within a specific namespace. In practice, this means that the service account the application is running as can be assigned either a `ClusterRole`, or a namespace-scoped `Role`. In the latter scenario, cluster-wide permissions specified by test cases are ignored. See [Writing Definitions](writing-definitions.md) on how this is specified. Depending on the mode of operation desired, the RBAC policy is generated as follows:

```bash
# Cluster-wide operation
$ poetry run ./generator.py rbac-policy > ../policy.yml
Generating ClusterRole with 20 permissions

# Namespace-scoped operation
# set the target namespace in generator/config.yml
$ poetry run ./generator.py rbac-policy --role > ../policy.yml
Generating Role with 16 permissions (ignored 4 clusterwide permissions)
```

## Running the Leonidas API Locally

It is possible to build and run the Leonidas Python API locally for development purposes. To do this:

* `cd generator`
* `poetry install` 
* `poetry run ./generator.py generate-aws-api` and/or `generate-kube-api`
* `cd ../output/leonidas`
* `poetry install`
* `poetry run python leonidas.py`

This will spawn the API listening at http://127.0.0.1:5000. By default, this uses whichever AWS credentials are configured as the default profile in `~/.aws/config`, and whichever Kubernetes credentials found in the default Kubeconfig. These can be overridden by supplying a role ARN to assume, access keys, JWT tokens or TLS client certificates to use for requests to the API.


