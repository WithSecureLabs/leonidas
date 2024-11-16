# Using Leonidas

## Authenticating to Leonidas

Requests to any endpoint that will execute an action requires that an API key be supplied. 2 API keys are automatically generated as part of the deployment process. To acquire an API key:

* `aws apigateway get-api-keys`, note the `id` field from the key you need the secret for
* `aws apigateway get-api-key --include-value --api-key [KEY-ID] | jq -r .value`
* These API keys can be supplied with requests by setting the `x-api-key` header on any requests made to Leonidas

## Executing Test Cases

Test cases are executed by making post requests to the API. Visiting the URL discussed above will present an OpenAPI interface, which will explain the different endpoints, parameters that can be passed and so on. The OpenAPI interface will also provide example curl commands that can be executed on the command line. You'll need to add the following argument to any curl commands so that the API gateway accepts the request, where `APIKEY` is the API key gathered in the previous section:

`-H "x-api-key: APIKEY"`

In addition, an OpenAPI definition file is available at `/swagger.json`. This can be imported into Postman, Insomnia and other common API development tools, which can then also be used to execute these test cases.

## Leo - Test Case Orchestrator

Leo is a helper script designed to make it easier to execute killchains as a whole, as opposed to individual test cases. To execute a suite of test cases in Leonidas in an automated fashion. To set Leo up, run the following:

* `pip install poetry`
* `cd ./leo`
* `poetry install`

To generate the config file for Leo:

* `cd generator && poetry run python generator.py leo` to generate the test case definitions for Leo
* `cp ./output/caseconfig/caseconfig.yml ./leo`
* edit the `caseconfig.yml` file in `./leo` to set the URL, API gateway API key, and to modify/reorder/remove test cases as required

To execute the cases you've configured:

* `poetry run ./leo.py caseconfig.yml`

## Identity Management

### AWS
Leonidas, by default, will execute test cases using the role assigned to the serverless function. For AWS, This role is created with a policy that contains all the permissions listed as necessary in the test case, along with `sts:AssumeRole`. However, it also supports two alternative mechanisms to execute test cases under a different identity

#### Role Assumption

It is possible to execute test cases as an arbitrary role by submitting the `role_arn` parameter as part of a request. This should be set to the ARN of the the role to be assumed.

#### AWS Access Keys

Submitting `access_key_id` and `secret_access_key` parameters containing the Access Key ID and Secret Access Key respectively will cause Leonidas to execute a test case using those credentials.

#### Region-specific test case execution

By default, test cases will run in the region in which the API is deployed, or in the default region specified in ~/.aws/config line if the API is running locally. It is possible to suppy a `region` parameter to the API, which will result in the test case being executed against that region. This parameter should contain the AWS region identifier, such as `us-east-1` or `eu-west-1`.


### Kubernetes
The Leonidas pod runs in the context of a Service Account, which is bound to a ClusterRole by default. Alternatively, to operate with permissions over a certain namespace only, it can be bound to a Role as described in [Deploying Leonidas](deploying-leonidas#building-and-deploying-the-api).

#### Tokens & Certificates
Other than the default Leonidas Service Account, test cases can be executed in the context of any other service account or cluster user, by providing the respective credentials as API parameters.

In detail, 
- to execute as another Service Account or user that authenticates via token authentication, provide the JWT value in the `token` URL parameter
- to execute as a cluster user which authenticates via X509 Client Certificate, provide the Base64-encode of the Certificate and Private Key, via the `tls_cert` and `tls_key` URL parameters respectively. The encoded version of a file can be obtained with a command such as: 
```bash
cat user1.key | base64 -w0 
```

