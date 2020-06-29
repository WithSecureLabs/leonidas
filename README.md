# Leonidas

This is the repository containing Leonidas, a framework for executing attacker actions in the cloud. It provides a YAML-based format for defining cloud attacker tactics, techniques and procedures (TTPs) and their associated detection properties. These definitions can then be compiled into:

* A web API exposing each test case as an individual endpoint
* Sigma rules (https://github.com/Neo23x0/sigma) for detection
* Documentation  - see http://detectioninthe.cloud/ for an example

![Leonidas Architecture](./docs/architecture.png?raw=true "Leonidas Architecture")

## Deploying the API

The API is deployed via an AWS-native CI/CD pipeline. Instructions for this can be found at [Deploying Leonidas](./docs/deploying-leonidas.md).

## Using the API

The API is invoked via web requests secured by an API key. Details on using the API can be found at [Using Leonidas](./docs/using-leonidas.md)

## Installing the Generator Locally

To build documentation or Sigma rules, you'll need to install the generator locally. You can do this by:

* `cd generator`
* `poetry install`

## Generating Sigma Rules

Sigma rules can be generated as follows:

* `poetry run ./generator.py sigma`

The rules will then appear in `./output/sigma`

## Generating Documentation

The documentation is generated as follows:

* `poetry run ./generator.py docs`

This will produce markdown versions of the documentation available at `output/docs`. This can be uploaded to an existing markdown-based documentation system, or the following can be used to create a prettified HTML version of the docs:

* `cd output`
* `mkdocs build`

This will create a `output/site` folder containing the HTML site. It is also possible to view this locally by running `mkdocs serve` in the same folder.

## Writing Definitions

The definitions are written in a YAML-based format, for which an example is provided below. Documentation on how to write these can be found in [Writing Definitions](./docs/writing-definitions.md)

```yaml
---
name: Enumerate Cloudtrails for a Given Region
author: Nick Jones
description: |
  An adversary may attempt to enumerate the configured trails, to identify what actions will be logged and where they will be logged to. In AWS, this may start with a single call to enumerate the trails applicable to the default region.
category: Discovery
mitre_ids:
  - T1526
platform: aws
permissions:
  - cloudtrail:DescribeTrails
input_arguments:
executors:
  sh:
    code: |
      aws cloudtrail describe-trails
  leonidas_aws:
    implemented: True
    clients:
      - cloudtrail
    code: |
      result = clients["cloudtrail"].describe_trails()
detection:
  sigma_id: 48653a63-085a-4a3b-88be-9680e9adb449
  status: experimental
  level: low
  sources:
    - name: "cloudtrail"
      attributes:
        eventName: "DescribeTrails"
        eventSource: "*.cloudtrail.amazonaws.com"
```

## Credits

Project built and maintained by Nick Jones ( [NJonesUK](https://github.com/NJonesUK) / [@nojonesuk](https://twitter.com/nojonesuk)).

This project drew ideas and inspiration from a range of sources, including:

* [Pacu](https://github.com/RhinoSecurityLabs/pacu)
* [Rhino Security's AWS IAM Privilege Escalations](https://github.com/RhinoSecurityLabs/AWS-IAM-Privilege-Escalation)
* All of Scott Piper's AWS security work ( [https://github.com/0xdabbad00](https://github.com/0xdabbad00) / [@0xdabbad00](https://twitter.com/0xdabbad00) )
* [MITRE ATT&CK](https://attack.mitre.org/matrices/enterprise/)
* [MITRE CALDERA](https://github.com/mitre/caldera)
* [Red Canary's Atomic Red Team](https://github.com/redcanaryco/atomic-red-team)
* [Sigma](https://github.com/Neo23x0/sigma)
