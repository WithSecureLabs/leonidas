#!/usr/bin/env python

"""
Leo - case executor for Leonidas. Takes a config file as its first argument.
"""


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
        url = config["url"] + config["cases"][case]["path"]
        headers = {}
        # if we're running Leonidas locally, no need for an API key, so let's not error out if there's not one in the config
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
        
        # TODO: Support access keys here
        if ("creds" in config) and (config["creds"] is not None):
            if "role_arn" in config["creds"]:
                args["role_arn"] = config["creds"]["role_arn"]
        print(config["cases"][case]["name"])

        # If it's a request with parameters it'll need to be POSTed, otherwise it's a GET request
        if ("args" in config["cases"][case]) and (config["cases"][case]["args"] is not None):
            r = requests.post(url, headers=headers, params=args)
        else:
            r = requests.get(url, headers=headers, params=args)
        print(json.dumps(r.json(), indent=4, sort_keys=True))

        # Sleep between cases
        time.sleep(config["sleeptime"])

    print("Ran {} test cases".format(len(config["cases"])))
