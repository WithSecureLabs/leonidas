#!/usr/bin/env python

"""
Leo - case executor for Leonidas. Takes a config file as its first argument.
"""


import datetime
import json
# import logging
import sys
import time

import requests
import yaml

class Client(object):
    def __init__(self, url, apikey = None, casefile = "./caseconfig.yml"):
        self.url = url
        self.apikey = apikey
        self.cases = self.load_cases(casefile)

    def load_cases(self, casefile):
        config = yaml.safe_load(open(casefile, "r"))
        return config["cases"]

    def get_identity(self, creds):
        ret_value = {}
        if ("role_arn" in creds) and (creds["role_arn"] != ""):
            ret_value["role_arn"] = creds["role_arn"]
        elif ("access_key_id" in creds) and (creds["secret_access_key"] != ""):
            ret_value["access_key_id"] = creds["access_key_id"]
            ret_value["secret_access_key"] = creds["secret_access_key"]
        if ("region" in creds) and (creds["region"] != ""):
            ret_value["region"] = creds["region"]
        return ret_value

    def run_case(self, path, args = {}, creds = {}):
        case_url = self.url + path
        # if we're running Leonidas locally, no need for an API key, 
        # so let's not error out if there's not one in the config
        headers = {}
        try:
            headers["x-api-key"] = self.apikey
        except Exception as e:
            print(e)
        # If it's a request with parameters it'll need to be POSTed, otherwise it's a GET request
        if (args != {}) and (args != None):
            args.update(self.get_identity(creds))
            r = requests.post(case_url, headers=headers, params=args)
        else:
            args.update(self.get_identity(creds))
            r = requests.get(case_url, headers=headers, params=args)
        print(json.dumps(r.json(), indent=4, sort_keys=True))
        return r.json()
