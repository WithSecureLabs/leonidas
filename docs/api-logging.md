# Leonidas API Logging

For each test case executed, Leonidas will create a log entry for that particular execution. The format of this is shown below.

```json
{
  "request": {
    "usecase": "/discovery/sts_get_caller_identity",
    "args": {},
    "timestamp": "2020-06-24 00:28:24.737414",
    "identity": {
      "assume_role": false,
      "role_arn": null,
      "access_keys": false,
      "access_key_id": null,
      "secret_access_key": null
    }
  },
  "response": {
    "UserId": "AROAYLGRIBRQ4IFAQ5OF2:botocore-session-1592951303",
    "Account": "573816966241",
    "Arn": "arn:aws:sts::573816966241:assumed-role/OrganizationAccountAccessRole/botocore-session-1592951303",
    "ResponseMetadata": {
      "RequestId": "a9d1bf24-f554-4c26-8c4b-7797a6307f1c",
      "HTTPStatusCode": 200,
      "HTTPHeaders": {
        "x-amzn-requestid": "a9d1bf24-f554-4c26-8c4b-7797a6307f1c",
        "content-type": "text/xml",
        "content-length": "490",
        "date": "Tue, 23 Jun 2020 22:28:24 GMT"
      },
      "RetryAttempts": 0
    }
  }
}
```

Each log entry contains:

* `request`: Defines what test case was triggered and how
  * `usecase`: Which test case was executed
  * `args`: Any parameters passed to the request
  * `timestamp`: The time at which the test case was executed, as returned by Python's `datetime.datetime.now(tz=datetime.timezone.utc)`
  * `identity`: The identity block for this test case, as defined in [writing-api-executors.md](./writing-api-executors.md)
* `response`: The contents of the `result` variable, as discussed in [writing-api-executors.md](./writing-api-executors.md)

## Accessing the Logs

When the API is deployed via the pipeline, the logs are delivered to a CloudWatch Log Group named `/aws/lambda/leonidas-dev-app`. These can be accessed via the AWS console, or by using the following CLI commands:

* `aws logs describe-log-streams --log-group-name /aws/lambda/leonidas-dev-app`
* `aws logs get-log-events --log-group-name /aws/lambda/leonidas-dev-app --log-stream-name [LOG-STREAM-NAME]`

Where `[LOG-STREAM-NAME]` is taken from the list of log streams returned by `aws logs describe-log-streams`. Note that special characters need to be escaped, else an error will be raised stating that the stream cannot be found.
