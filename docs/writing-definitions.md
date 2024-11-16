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

One of the categories, or tactics, from the MITRE ATT&CK framework. Consider both the [Enterprise](https://attack.mitre.org/tactics/enterprise/) and [Cloud](https://attack.mitre.org/matrices/enterprise/cloud/) matrices. 

## mitre_ids

A YAML list of MITRE ATT&CK IDs that apply to the test case.

## platform

The cloud platform the test case is designed for. Can be either `aws` or `kubernetes`.

## permissions
A yaml list of permissions required for the test case to correctly execute. 

In the case of AWS, these should be the individual IAM permissions required, rather than the name of a managed or custom policy that contains the necessary permissions. 

In Kubernetes test cases, the `permissions` field is a list of items, each consisting of four parameters, as shown in the example below:
```yml
      permissions:
      - namespaced: true
        apiGroups: [""]
        resources:
        - serviceaccounts
        verbs:
        - create
```
For every permission, it must be specified whether the test case should be performed in a namespace context or cluster-wide (`namespaced` parameter). The remaining parameters for each permission needed are declared according to the Kubernetes [RBAC rule format](https://kubernetes.io/docs/reference/access-authn-authz/rbac/).

The `permissions` field of the definition is mandatory. Kubernetes test cases that do not require any permissions, can specify the following "empty" block:

```yml
	  - namespaced: true
        apiGroups: [""] 
		resources: [""]
		verbs: [""]
```

## input_arguments

A YAML dictionary of arguments required for the test case to be successfully executed. These are made available by name as HTTP POST parameters to the API, and then as variables named according to their name here within the `leonidas_aws` executor. Each argument has the following three fields:

### description

A text description of the parameter, which should be sufficient to indicate to someone using the test case what data they should pass in.

The description should explain the default behaviour when no value is provided, as seen in the following test case:
```yml
name: Writeable hostPath Mount
category: "Privilege Escalation"
description: "Create a container with a writeable hostPath mount"
platform: kubernetes
input_arguments:
  custom_yaml:
    description: |
	    YAML manifest for the pod - leave this empty to use the default spec that performs the TTP
    type: file
    value: 
      apiVersion: v1
      kind: Pod
      spec:
        volumes:
        - name: host-fs
          hostPath:
            path: /
        containers:
        - image: ubuntu
          name: attacker-pod
          command: ["/bin/sh", "-c", "sleep infinity"]
          volumeMounts:
          - name: host-fs
            mountPath: /host
        restartPolicy: Never
```

### type

The data type that the parameter should match. Currently supported types are
- `str` 
- `int`
- `file`

If the argument is of type `file`, it must be named `custom_yaml`.

### value

A default value for the argument.

If the argument is of type `file`, the argument's value can be uploaded using a `Content-Type: multipart/form-data` , or specified in YAML within the test case's fields. 

The final YAML will be saved within the container in `/tmp/custom.yml`, and fed into the `kubectl -f apply` command, as shown in the example above.

## Executors

A YAML dictionary of executors, which define how to execute a given test case. The currently supported executors are:

- `sh`: the CLI command to execute the test case standalone
- `leonidas_aws`: the Python attack definition that is baked into the Leonidas web API
- `leonidas_kube`: only used to hold the [`implemented`](#implemented) status of the test case. Code for Kubernetes test cases must be specified in the `sh` executor field instead

### sh

The `sh` executor has one single field, `code`. This is a multi-line string that defines the CLI command(s) to run. This field is used as part of the test case documentation produced by the framework. 

In the case of Kubernetes attack defitions, this field is also used as the test case code. It is rendered using a jinja2 template, and therefore template variables (like `{{ serviceaccount }}`) are replaced with the values specified in  `input_arguments`, or default values from `input_arguments.value`

For Kubernetes, if the user has specified an identity for Leonidas to assume (passing a service account token or client certificate and key) then `kubectl` within the shell command will be replaced programmatically to `kubectl --kubeconfig`, passing a temporary configuration file holding these credentials. Read more in [Identity Management](using-leonidas.md#identity-management).

### leonidas_aws

The executor which defines the test case that will be embedded into the Leonidas web API as part of the code generation. This defines three required fields: `implemented`, `clients` and `code`.

#### implemented

This instructs the generator whether to include this test case. This should be set to `True` where you are happy with the implementation of this test case and are ready to deploy it as part of the Leonidas API, or `False` if not.

#### clients

A YAML list of names of boto3 clients to make available to the python code. These client names must match the strings passed to `boto3.Client()`, and are documented in the boto3 documentation at

By way of example, to create an IAM client, specify `iam` as one of the list items here. Under the hood, this will instantate a boto3 IAM client as below:

```
client = boto3.client('iam')
```

#### code

For the AWS executor, `code` should specify a multi-line YAML string defining the python code to embed as an API endpoint in the Leonidas AWS API. For guidance on how to implement test cases to work with the Leonidas API, see [Writing API Executors](writing-api-executors.md).



### leonidas_kube

Executor block indicating whether the test case should be embedded into the Leonidas web API as part of the code generation. The only required field is `implemented`. The kubernetes executor resorts to shell execution within the pod, allowing for simple `kubectl` invocations like `kubectl get deployments`. As such, the `code` value of the `sh` block is used for this executor. 

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

The name of the source. For AWS, at present this is usually `cloudtrail`, while for Kubernetes, a source of `audit` will translate to the novel Sigma logsource for Kubernetes Audit logs: 
```yaml
logsource:
  product: kubernetes
  service: audit
```

#### attributes

Key-value pairs of field and field value to search for to identify instances of a given event. 

For cloudtrail, the attributes are typically:

* `eventName` - this field is the name of the event, and typically (though not always) matches the name of the permission to undertake the action
* `eventSource` - this field is set to the AWS service that the action is associated with, and typically comes in the form `REGION.SERVICENAME.amazonaws.com`. To avoid detections being limited to single regions, the region portion should typically be set to `*`

For Kubernetes audit logs, the attributes supported are listed below. Applying the custom pipeline upon the Sigma definitions generated, these fields are then mapped to the respective fields used by the [ELK Kubernetes Integration](https://docs.elastic.co/en/integrations/kubernetes)

- `verb` - e.g. "create"
	- This will be mapped by the pipeline to the `kubernetes.audit.verb` field
- `apiGroup` - set to "" for the default API group, or e.g. "authorization.k8s.io" for a non-default API group
	- This will be mapped by the pipeline to the `kubernetes.audit.objectRef.apiGroup` field
	- If omitted, or set to an empty value (''), the pipeline will drop it from the subsequent SIEM queries as the ELK Kubernetes integration doesn't set this field for events relating to the default apiGroup 
- `resource` - e.g. "pods"
	- This will be mapped by the pipeline to the `kubernetes.audit.objectRef.resource` field
- `subresource` - will be omitted unless a sub-resource is targeted e.g. "exec" for "pod/exec" actions
	- This will be mapped by the pipeline to the `kubernetes.audit.objectRef.subresource` field 
	- If omitted, or set to an empty value (''), the pipeline will drop it from the subsequent SIEM queries as the ELK Kubernetes integration doesn't set this event field for resource-only endpoints 
	- If omitted, it will be omitted from the Sigma and subsequent SIEM queries   
- `namespace` - set to "" for any namespace, or e.g. "kube-system" for a specific namespace
	- This will be mapped by the pipeline to the `kubernetes.audit.objectRef.namespace` field
	- If omitted, it will be omitted from the Sigma and subsequent SIEM queries
- `capabilities` - will be set to the empty value ('') for most use cases, or `"*"` to look for not-null values
	- This will be mapped by the pipeline to the `kubernetes.audit.requestObject.spec.containers.securityContext.capabilities.add` field
	- If omitted, it will be omitted from the Sigma and subsequent SIEM queries