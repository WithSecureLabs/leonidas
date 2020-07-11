# Writing your own case definitions

Each definition contains a number of fields, these are broken down in this document. 

## Validating Test cases

It's possible to run some basic validation on your new test cases with the following command. This will spot missing fields primarily, but may also catch some syntax errors in the python executor definitions.

* `poetry run ./generator.py validate`

## Template contents

An example template is shown below.

```yaml
---
name: Access Secret in Secrets Manager
author: Nick Jones
description: |
  An adversary may attempt to access the secrets in secrets manager, to steal certificates, credentials or other sensitive material
platform: aws
category: Credential Access
mitre_ids:
  - T1528
permissions:
  - secretsmanager:GetSecretValue
  - kms:Decrypt
input_arguments:
  secretid:
    description: ID of secret to access, either ARN or friendly name
    type: str
    value: "leonidas_created_secret"
executors:
  sh:
    code: |
      aws secretsmanager get-secret-value --secret-id {{ secretid }}
  leonidas_aws:
    implemented: True
    clients:
      - secretsmanager
    code: |
      result = clients["secretsmanager"].get_secret_value(SecretId=secretid)
detection:
  sigma_id: cbeba6f0-019e-4782-8c7e-e21b10521eed
  status: experimental
  level: low
  sources:
    - name: "cloudtrail"
      attributes:
        eventName: "GetSecretValue"
        eventSource: "*.secretsmanager.amazonaws.com"
```

## name

The full name of the test case

## author

The person writing the case. Can be multiple, separated by commas

## description

A description of the test case

## category

One of the categories, or tactics, from the MITRE ATT&CK framework. The list is here: https://attack.mitre.org/tactics/enterprise/

## mitre_ids

A YAML list of MITRE ATT&CK IDs that apply to the test case.

## platform

The cloud platform the test case is designed for. At present, Leonidas only supports AWS, however documentation will be generated for other platforms

## permissions

A yaml list of permissions required for the test case to correctly execute. In the case of AWS, these should be the individual IAM permissions required, rather than the name of a managed or custom policy that contains the necessary permissions.

## input_arguments

A YAML dictionary of arguments required for the test case to be successfully executed. These are made available by name as HTTP POST parameters to the API, and then as variables named according to their name here within the `leonidas_aws` executor. Each argument has the following three fields:

### description

A text description of the parameter, which should be sufficient to indicate to someone using the test case what data they should pass in.

### type

The data type that the parameter should match. Currently supported types are `str` and `int` - anything not an integer should be `str`

### value

A default value for the parameter.

## Executors

A YAML dictionary of executors, which define how to execute a given test case. There are currently two supported executors:

- `leonidas_aws`: the attack definition that is baked into the Leonidas web API
- `sh`: the CLI command to execute the test case standalone

### sh

The `sh` executor has one single field, `code`. This is a multi-line string that defines the CLI command to run. This field is used as part of the test case documentation produced by the framework. It is rendered as a jinja2 template, and as such jinja2 variables named to match parameters listed in `input_arguments` for the case will be replaced by their default value.

### leonidas_aws

The executor which defines the test case that will be embedded into the Leonidas web API as part of the code generation. This defines three required fields.

#### implemented

This instructs the generator whether to include this test case. This should be set to `True` where you are happy with the implementation of this test case and are ready to deploy it as part of the Leonidas API, or `False` if not.

#### clients

A YAML list of names of boto3 clients to make available to the python code. These client names must match the strings passed to `boto3.Client()`, and are documented in the boto3 documentation at

By way of example, to create an IAM client, specify `iam` as one of the list items here. Under the hood, this will instantate a boto3 IAM client as below:

```
client = boto3.client('iam')
```

#### code

A multi-line YAML string defining the python code to embed as an API endpoint in the Leonidas AWS API. For guidance on how to implement test cases to work with the Leonidas API, see `writing-api-executors.md` in this directory.

## detection

The block defining detection characteristics, from which Sigma rules and ELK queries are generated. 

### sigma_id

A randomly generated GUID to serve as an identifier for any Sigma rules generated.

### status

Used by sigma to indicate maturity of the rule. Should be set to one of the following:

* `experimental`: could lead to false positives or be noisy, but could also identify interesting events.
* `test`: an almost stable rule that might require some fine tuning.
* `stable`: considered ready to be used used in production systems or dashboards.

### level

Indication of how critical the event is from a detection perspective. Should be set to one of the following:

* `low`
* `medium`
* `high`
* `critical`

Given the nature of these test cases, it is expected that the majority will be set to `low` or `medium`, and used to inform an overall detection picture rather than triggering alerts directly.

### sources

The sources block defines where to look to identify incidents of this event.

#### name

The name of the source. For AWS, at present this is usually `cloudtrail`.

#### attributes

Key-value pairs of field and field value to search for to identify instances of a given event. For cloudtrail, the attributes are typically:

* `eventName` - this field is the name of the event, and typically (though not always) matches the name of the permission to undertake the action
* `eventSource` - this field is set to the AWS service that the action is associated with, and typically comes in the form `REGION.SERVICENAME.amazonaws.com`. To avoid detections being limited to single regions, the region portion should typically be set to `*`
