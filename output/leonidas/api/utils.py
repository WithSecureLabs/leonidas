from datetime import date, datetime
import base64
import enum
import json
import os
import re
import subprocess
import traceback

import boto3

import jinja2
import werkzeug
from flask_restx import reqparse

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

class ID_TYPE(enum.Enum):
    ID_LEONIDAS   = 0
    ID_SA         = 1
    ID_USER       = 2

class KubeCredentials:
    """Class with utilities related to the processing of Kubernetes credentials supplied by the user"""
    
    def __init__(self, request):
        self.CUSTOM_KUBECONFIG_PATH = "/tmp/custom-kubeconfig"
        self.identity_to_use = ID_TYPE.ID_LEONIDAS
        
        self.token    = request.args.get("token")
        self.tls_cert = request.args.get("tls_cert")
        self.tls_key  = request.args.get("tls_key")

        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader("api"),
        ) 

    def validate_creds(self):
        """
        Validates any Kubernetes credentials passed.
        Decides the Identity that should be used.
        Raises Exceptions if logic errors are found.
        """
        if not any([self.token, self.tls_cert, self.tls_key]):              # no cred passed : Leonidas ID
            self.identity_to_use = ID_TYPE.ID_LEONIDAS
            return
        elif self.token:
            if self.tls_cert or self.tls_key:                               # token & (cert | key) : Error
                raise TypeError('Can only assume identity of service account or user, not both')
            else:                                                           # just token : SA ID
                # JWT input field validation
                if not re.findall(r'(^eyJ[\w-]+\.eyJ[\w-]+\.[\w-]+$)',self.token):
                    raise ValueError('Token provided in unexpected format')
                self.identity_to_use = ID_TYPE.ID_SA
                return
        else:
            if (bool(self.tls_cert) != bool(self.tls_key)):                 # no token & (cert ^ key) : Error
                raise ValueError('Need both tls_cert and tls_key to assume user identity')
            else:                                                           # no token & (cert & token) : User ID
                self.identity_to_use = ID_TYPE.ID_USER
        

    def pass_creds(self, exec_code, phase, case):
        """
        Configures a temp kubeconfig & any custom credentials prior to kubectl execution, if a SA or User identity is assumed. 
        Then wraps kubectl with a --kubeconfig pointing to the temp file for execution.
        """
        if self.identity_to_use == ID_TYPE.ID_LEONIDAS: # NOOP
            return exec_code
        else:
            kubeconfig_tpl = self.env.get_template("kubeconfig.jinja2")
            server="https://{}:{}".format(
                os.environ["KUBERNETES_SERVICE_HOST"],
                os.environ["KUBERNETES_SERVICE_PORT"] 
            )
            
            if self.identity_to_use == ID_TYPE.ID_SA:
                kubeconfig = kubeconfig_tpl.render(server=server, token="token: "+self.token )
            
            elif self.identity_to_use == ID_TYPE.ID_USER:
                tmpname = (phase+'_'+case).lower()
                self.tmpcert, self.tmpkey = '/tmp/'+tmpname+'.crt' , '/tmp/'+tmpname+'.key'
                with open(self.tmpcert,'w') as c, open(self.tmpkey,'w')  as k:
                    c.write(base64.b64decode(self.tls_cert).decode('utf-8'))
                    k.write(base64.b64decode(self.tls_key).decode('utf-8'))
                kubeconfig = kubeconfig_tpl.render(
                    server=server, 
                    cert="client-certificate: "+self.tmpcert, 
                    key="client-key: "+self.tmpkey
                )

            with open(self.CUSTOM_KUBECONFIG_PATH, "w") as f:
                f.write(kubeconfig)
            return exec_code.replace('kubectl','kubectl --kubeconfig '+self.CUSTOM_KUBECONFIG_PATH)
        
    
    def cleanup_creds(self):
        """
        Removes any test case credentials from the container's filesystem as well as the temp kubeconfig (reverting to in-cluster configuration) 
        """
        self.tls_cert = self.tls_key = self.token = None
        if not self.identity_to_use == ID_TYPE.ID_LEONIDAS:
            os.remove(self.CUSTOM_KUBECONFIG_PATH)
            if self.identity_to_use == ID_TYPE.ID_USER:
                os.remove(self.tmpcert), os.remove(self.tmpkey)
            
        
class FileParser:  
    parser = reqparse.RequestParser()
    parser.add_argument('custom_yaml',  
                        type=werkzeug.datastructures.FileStorage, 
                        location='files',  
                        help='YAML manifest')
