from datetime import date, datetime
import json
import traceback
import boto3


class JSONEncoder(json.JSONEncoder):
    """
    Extend flask's json-encoder class to work with return calls
    """

    def default(self, o):
        if isinstance(o, set):
            return list(o)
        if isinstance(o, (datetime, date)):
            return str(o)
        if isinstance(o, Exception):
            return str(o)
        return json.JSONEncoder.default(self, o)


class Config:
    RESTX_JSON = {"cls": JSONEncoder}


def json_serial(obj):
    """
    JSON serializer for objects not serializable by default json code
    """
    if isinstance(obj, set):
        return list(obj)
    if isinstance(obj, (datetime, date)):
        return str(obj)
    if isinstance(obj, Exception):
        return str(obj)
    raise TypeError("Type %s not serializable" % type(obj))


def aws_define_identity(request):
    """
    Return an identity dictionary based on the role arns, creds etc that have been passed into the request.
    """
    identity = {
        "assume_role": False,
        "role_arn": None,
        "access_keys": False,
        "access_key_id": None,
        "secret_access_key": None,
        "region": None
    }
    try:
        identity["role_arn"] = request.args.get("role_arn")
        if identity["role_arn"]:
            identity["assume_role"] = True
    except Exception:
        traceback.print_exc()
    try:
        identity["access_key_id"] = request.args.get("access_key_id")
        identity["secret_access_key"] = request.args.get("secret_access_key")
        if identity["access_key_id"] and identity["secret_access_key"]:
            identity["access_keys"] = True
    except Exception:
        traceback.print_exc()

    try:
        session = boto3.session.Session()
        default_region = session.region_name
        identity["region"] = request.args.get("region") or default_region
    except Exception:
        traceback.print_exc()    

    return identity


def get_clients(identity, client_list):
    """
    Return a dictionary of clients based on the identity dictionary passed in
    """
    clients = {}
    for client in client_list:
        if identity["assume_role"]:
            clients[client] = get_client_roleassumption(client, identity["role_arn"], identity["region"])
        elif identity["access_keys"]:
            clients[client] = get_client_accesskey(
                client, identity["access_key_id"], identity["secret_access_key"], identity["region"]
            )
        else:
            clients[client] = boto3.client(client, identity["region"])
    return clients


def get_client_roleassumption(service, role_arn, region, session_name="LeonidasSession"):
    """
    Assume a role, then return the relevant client.

    service: the service to return a client for, to match the string passed to boto3.client()
    role_arn: the ARN of the role to be assumed
    """
    sts_client = boto3.client("sts")
    creds = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=session_name)[
        "Credentials"
    ]

    return boto3.client(
        service,
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
        region_name=region
    )


def get_client_accesskey(service, access_key_id, secret_access_key, region):
    """
    Return a client for a given service using a supplied access key

    service: the service to return a client for, to match the string passed to boto3.client()
    access_key_id: the access key id for the access key to use, typically supplied in the AccessKeyId field
    secret_access_key: the secret access key for the access key to use, typically supplied in the SecretAccessKey field
    """
    return boto3.client(
        service,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region
    )
