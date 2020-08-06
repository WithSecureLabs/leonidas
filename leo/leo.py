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

if __name__ == "__main__":
    config = yaml.safe_load(open(sys.argv[1], "r"))
    print("Url: {}".format(config["url"]))
    for case in config["cases"]:
        print("[{0} UTC] {1}".format(datetime.datetime.utcnow(), config["cases"][case]["name"]))
        url = config["url"] + config["cases"][case]["path"]
        headers = {}
        # if we're running Leonidas locally, no need for an API key, 
        # so let's not error out if there's not one in the config
        try:
            headers["x-api-key"] = config["apikey"]
        except KeyError:
            continue

        # Grab the args from the case
        if "args" in config["cases"][case]:
            if config["cases"][case]["args"]:
                args = config["cases"][case]["args"]
            else:
                args = {}
        else:
            args = {}

        # load any credentials and region details configured in the caseconfig
        if ("identity" in config) and (config["identity"] is not None):
            if "role_arn" in config["identity"]:
                args["role_arn"] = config["identity"]["role_arn"]
            elif ("access_key_id" in config["identity"]) and ("secret_access_key" in config["identity"]):
                args["access_key_id"] = config["identity"]["access_key_id"]
                args["secret_access_key"] = config["identity"]["secret_access_key"]
            if "region" in config["identity"]:
                args["region"] = config["identity"]["region"]

        # If it's a request with parameters it'll need to be POSTed, otherwise it's a GET request
        if ("args" in config["cases"][case]) and (config["cases"][case]["args"] is not None):
            r = requests.post(url, headers=headers, params=args)
        else:
            r = requests.get(url, headers=headers, params=args)
        print(json.dumps(r.json(), indent=4, sort_keys=True))

        # Sleep between cases
        time.sleep(config["sleeptime"])

    print("Ran {} test cases".format(len(config["cases"])))
