import ast
from collections import defaultdict
import json
import os
import re
import sys
import time
import traceback

import jinja2
import yaml


class Definitions:
    """
    Holds the definitions for the attacker actions on which the generator executes
    """

    def __init__(self, config, env):
        self.definitions_path = config["definitions_path"]
        self.config = config
        self.env = env
        self.case_set = []
        self.categories = set()
        self.permissions = defaultdict(set)
        self.casecount = 0
        self.templates = {}
        self.templates["aws_sigma"] = env.get_template(
            os.path.join("aws", "sigma.jinja2")
        )
        self.templates["kube_sigma"] = env.get_template(
            os.path.join("kubernetes", "sigma.jinja2")
        )
        self._file_list = []
        self._validator = defaultdict(dict)
        self._validator["case"] = {
            "name": "Case {} is missing a name",
            "description": "Case {} is missing a description",
            "category": "Case {} has no category name",
            "mitre_ids": "Case {} has no associated MITRE IDs",
            "platform": "Case  {} does not define a platform",
            "permissions": "Case {} does not define the permissions required for execution",
            "input_arguments": "Case {} does not define input arguments. Note that this key must exist, even if it is empty",
            "executors": "Case {} has no executors",
            "detection": "Case {} has no defined detections",
        }
        self._validator["aws"] = {
            "implemented": "Case {} is missing the implemented field in the leonidas_aws executor",
            "code": "Case number {} has a python executor but either no code, or the code present does not parse as valid Python",
            "clients": "Case number {} has a python executor but no clients defined",
        }
        self._validator["kube"] = {
            "code": "Case {} has no commandline defined",
            "perm_struct": "Invalid format of permissions structure for case {}",
            "verb": "Warning: Uncommon verb '{}' defined in the permissions of case {}. Review manually if it's valid"
        }
        self._validator["arg"] = {
            "description": "Argument number {} in case {} has no description",
            "type": "Argument number {} in case {} has no type",
            "value": "Argument number {} in case {} has no default value",
        }
        self._validator["filearg"] = {
            "filename": "File argument number {} in case {} is not named 'custom_yaml'",
            "fileyaml": "File argument number {} in case {} is not valid YAML"
        }
        self._validator["argdef"] = {
            "rfc": "Warning: Argument number {} in case {} does not comply with RFC 1123. If this is a resource name, it will be rejected by the API server.",
        }
        self._validator["detection"] = {
            "sigma_id": "Detection for case {} has no sigma_id field. This should be a unique GUID value",
            "status": 'Detection for case {} has no status set. This should be either "experimental", "test" or "production"',
            "level": 'Detection for case {} has no level set. This should be either "high", "medium" or "low"',
            "sources": "Detection for case {} needs at least one source",
        }
        # note: a complete listing of valid verbs can only be obtained by querying the cluster. This reduced list serves as a best-effort attempt to catch typos in permissions declaration, for rule that wll in fact be accepted at definition time but will fail with permission errors on runtime 
        self._common_verbs = ["create","get","list","delete","deletecollection","watch","update","patch","bind","escalate","impersonate","sign"]
        self._rfc1123regex = re.compile("[a-z0-9]([-a-z0-9]*[a-z0-9])?(\\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")

    def construct_definitions(self):
        """
        Loop over the yaml files in the definitions path supplied at runtime, parse and generate
        definitions from those files
        """
        self._construct_filelist()
        for item in self._file_list:
            filedata = yaml.safe_load(open(item, "r").read())
            try:
                filedata["last_modified"] = time.strftime(
                    "%Y-%m-%d", time.gmtime(os.path.getmtime(item))
                )
                self._generate_definitions(filedata)
            except Exception:
                traceback.print_exc(file=sys.stdout)
                continue

    def validate(self):
        """
        Build the file list, validate all the files
        """
        self._construct_filelist()
        validation_success = True
        for item in self._file_list:
            print("validating {}".format(item))
            filedata = yaml.safe_load(open(item, "r").read())
            if not self._validate_file(filedata, item):
                validation_success = False
            self.casecount = self.casecount + 1
        return validation_success

    def get_aws_policy(self):
        """
        Get an IAM policy based on the definitions
        """
        policy_template = self.env.get_template("iam-policy.jinja2")
        rendered = policy_template.render({"permissions": self.permissions["aws"]})
        return rendered
    
    def get_rbac_policy(self, role=False):
        """
        Get the YAML definition of a Kubernetes RBAC policy (ClusterRole or Role) with the permissions required by the definitions
        """
        policy_json = {
            "kind": "Role",
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "metadata": {},
            "rules": []
        }
        permissions_sd_list =  []
        ignored = 0
        if role: # prepare Role - namespaced operation
            policy_json["kind"] = "Role"
            policy_json["metadata"]["name"] = "leonidas-role"
            policy_json["metadata"]["namespace"] = self.config["namespace"]

            for p in self.permissions["kubernetes"]:
                pd = json.loads(p) 
                # json.loads is a hack to bypass the un-hashable dict items of the self.permission defaultdict, which is implemented as a set. Essentially, we serialise to string to squeeze it in, de-serialise when taking out to pass to jinja
                if pd["namespaced"]==True:
                    pd.pop('namespaced') 
                    permissions_sd_list.append(pd)
                else:
                    ignored = ignored + 1
        else:    # prepare ClusterRole - cluster-wide operation
            policy_json["kind"] = "ClusterRole"
            policy_json["metadata"]["name"] = "leonidas-clusterrole"

            for p in self.permissions["kubernetes"]:    
                pd = json.loads(p) 
                pd.pop('namespaced') 
                permissions_sd_list.append(pd)

        policy_json["rules"] = permissions_sd_list

        print("Generating {} with {} permissions{}".format(
            "Role" if role else "ClusterRole",
            len(permissions_sd_list),
            " (ignored "+str(ignored)+" clusterwide permissions)" if role else ""
        ),file=sys.stderr)

        rendered_yaml = yaml.dump(policy_json)
        return rendered_yaml

    def _validate_file(self, case, filename):
        """
        Perform validation on an individual YAML file based on the keys defined in the key dicts
        generated in __init__()
        """
        validation_success = True
        for key in self._validator["case"]:
            if key not in case.keys():
                validation_success = False
                print(self._validator["case"][key].format(filename))
        if "input_arguments" in case.keys():
            # Implement validation for input arguments having the correct fields too
            if case["input_arguments"]:
                argcount = 0
                for arg in case["input_arguments"]:
                    argcount = argcount + 1
                    argdict = case["input_arguments"][arg]
                    for key in self._validator["arg"]:
                        if key not in case["input_arguments"][arg]:
                            print(
                                self._validator["arg"][key].format(argcount, filename)
                            )
                    if argdict["type"]=="file":
                        if arg != "custom_yaml":
                            print(self._validator["filearg"]["filename"].format(argcount, filename))
                            validation_success = False
                    
                    # In Kubernetes, resource names must match RFC 1123
                    #   However, the validation below checks all args, which might not be resource names 
                    #   e.g. a command to be passed to "kubectl exec". Such values don't have to conform to RFC 1123
                    #   To accomondate this scenario, the validation below does not set the Fail switch, and prompts the user to check manually
                    #   TODO see #23 for fix strategies
                    if argdict["type"]=="str" and case["platform"]=="kubernetes":
                        if not self._rfc1123regex.match(argdict["value"]):
                            print(self._validator["argdef"]["rfc"].format(argcount,filename))
                            # validation_success = False
        if "executors" in case.keys():
            # Use ast.parse(source) to validate python code
            if "leonidas_aws" in case["executors"].keys():
                if case["executors"]["leonidas_aws"]["implemented"]:
                    try:
                        ast.parse(case["executors"]["leonidas_aws"]["code"])
                    except Exception:
                        print(self._validator["aws"]["code"].format(filename))
                        validation_success = False
                    try:
                        clients = case["executors"]["leonidas_aws"]["clients"]
                        if len(clients) == 0:
                            print(self._validator["aws"]["clients"].format(filename))
                            validation_success = False
                    except Exception:
                        print(self._validator["aws"]["clients"].format(filename))
                        validation_success = False
            if "leonidas_kube" in case["executors"].keys():
                if case["executors"]["leonidas_kube"]["implemented"]:
                    try:
                        code = case["executors"]["sh"]["code"]
                    except KeyError:
                        print(self._validator["kube"]["code"].format(filename))
                        validation_success = False
                    permissions = case["permissions"]
                    for p in permissions:
                        if not set(p.keys()) == set(["namespaced","apiGroups","resources","verbs"]):
                            print(self._validator["kube"]["perm_struct"].format(filename))
                            validation_success = False
                            break
                        # Check only verbs in RBAC rules, resources can be trickier. 
                        for v in p["verbs"]:
                            if v and v not in self._common_verbs:
                                print(self._validator["kube"]["verb"].format(v,filename))
                    
                        


        else:
            print("No executors defined in {}".format(filename))
            validation_success = False

        if "detection" in case.keys():
            for key in self._validator["detection"]:
                if key not in case["detection"].keys():
                    print(self._validator["detection"][key].format(filename))
                    validation_success = False

        return validation_success

    def _construct_filelist(self):
        """
        Get the list of yaml files in a given directory structure
        """
        for root, subdirs, files in os.walk(self.definitions_path):
            for item in files:
                if item.split(".")[-1] == "yml":
                    filepath = os.path.join(root, item)
                    if filepath not in self._file_list:
                        self._file_list.append(filepath)

    def _generate_definitions(self, case):
        """
        Construct the definitions given a specific file's data
        """
        self.categories.add(case["category"])
        if case["platform"] == "aws":
            for permission in case["permissions"]:
                self.permissions["aws"].add(permission)
            if "leonidas_aws" in case["executors"].keys():
                if case["executors"]["leonidas_aws"]["implemented"]:
                    case["executors"]["leonidas_aws"]["rendered"] = self._generate_aws_code(case)
            case["sigma"] = self.templates["aws_sigma"].render(case)
        if case["platform"] == "kubernetes":
            for permission in case["permissions"]:
                self.permissions["kubernetes"].add(json.dumps(permission))
                # json.dump is a hack to bypass the un-hashable dict items of the self.permission defaultdict, which is implemented as a set. Essentially, we serialise to string to squeeze it in, de-serialise when taking out to pass to jinja
            if "leonidas_kube" in case["executors"].keys():
                if case["executors"]["leonidas_kube"]["implemented"]:
                    case["executors"]["leonidas_kube"]["rendered"] = self._generate_kube_code(case)
            case["sigma"] = self.templates["kube_sigma"].render(case)
        self.case_set.append(case)

    def _generate_aws_code(self, case):
        exec_template = jinja2.Template(case["executors"]["leonidas_aws"]["code"])
        if case["input_arguments"]:
            exec_code = exec_template.render(case["input_arguments"])
        else:
            exec_code = exec_template.render({})
        return exec_code

    def _generate_kube_code(self, case):
        """
        Render the shell command(s) from the template in executors.sh.code, based on input_arguments
        """
        exec_template = jinja2.Template(case["executors"]["sh"]["code"])
        if case["input_arguments"]:
            file_default_yaml = case["input_arguments"].get("custom_yaml")
            if file_default_yaml:
                case["takes_file"] = True
                case["file_default_yaml"] = yaml.dump(file_default_yaml["value"])
                case["input_arguments"].pop("custom_yaml")
            # exec_code = exec_template.render(case["input_arguments"])
            kube_cli_render_args = { arg_name : "$"+arg_name for arg_name in case["input_arguments"] } 
            exec_code = exec_template.render(kube_cli_render_args)
        else:
            exec_code = exec_template.render({})
        return exec_code