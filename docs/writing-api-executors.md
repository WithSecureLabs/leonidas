# Implementing AWS test cases

The `code` block within the `leonidas_aws` section should contain the Python code necessary to execute a given test case within AWS. Typically, this will involve calling out to the AWS APIs via a boto3 client. This document outlines the libraries available and variables that are pre-populated for you, and how to correctly return the results such that they appear in the HTTP API response and also in the logs.

## Example test case code

```yaml
[...]
input_arguments:
  secretid:
    description: ID of secret to access, either ARN or friendly name
    type: str
    value: "leonidas_created_secret"
[...]
executors:
  leonidas_aws:
    implemented: True
    clients:
      - secretsmanager
    code: |
      result = clients["secretsmanager"].get_secret_value(SecretId=secretid)
```

## Available Variables and Objects

### `clients` 

A python dictionary containing each boto3 client defined by the `clients` parameter in the definition YAML.

Behind the scenes, Leonidas will handle assuming any roles or using any AWS access keys that are passed as parameters to the request. The clients available to the code are instantiated using the identity defined by the role or access key parameters. If none are supplied, it defaults to the role the lambda function is assigned (or the default profile specified in `~/.aws/config` if run locally)

### `identity`

A python dictionary defining the following fields: 
 
```python
{
        "assume_role": False, # Whether a role has been assumed to execute this case
        "role_arn": None, # If assume_role is True, the ARN of the role assumed
        "access_keys": False, # Whether IAM access keys have been passed to the function
        "access_key_id": None, # The access key ID supplied to the API call, if access_keys is set to True
        "secret_access_key": None, # The matching secret access key to the above key ID, if access_keys is set to True
}
```

This should generally not be used directly, as the framework uses this data to construct the boto3 clients available in the `clients` dictionary. It is, however, available if required.

### Case-specific input arguments

Arguments for a given test case are defined in the `input_arguments` field in the test case definition. These are made available to the test case code as local variables with the same names as the name used in the `input_arguments` block.

Under the hood, the generated API code sets the value of a given variable to the value passed to the API call, unless no value is passed in. If no value is supplied, the default value defined in the `input_arguments` block is used.

```python
secretid = request.args.get("secretid") or "leonidas_created_secret"
```

## Returning Data

The `result` variable should be set to the test case results. This is returned as a response to the HTTP request made to the API, and also logged as part of the case execution log by the function. The test case itself should not include a `return` statement, as this will interfere with Leonidas' logging and auditing capabilities.

# Implemented Azure Test Cases

Not yet supported

# Implementing Google Cloud Test Cases

Not yet supported
