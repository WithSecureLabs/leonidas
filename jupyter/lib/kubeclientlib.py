#!/usr/bin/env python

import requests
from datetime import datetime

class Client(object):
    def __init__(self, url, sa_token=None):
        self.url = url
        self.sa_token = sa_token
        self.execution_log = {}
        #  {
        #   timestamp: ["discovery/enumerate_pods", success],
        #   "duration": [50, 40, 45]
        # }

    def run_case(self, path, args=None, verb="get"):
        if args is None:
            args = {}
        case_url = self.url + path
        # Decide request verb in a semi-assisted way, as the client can't tell from just the arguments passed
        if ( args=={} or args is None ) and verb != "put":
            args.update({"token":self.sa_token})
            r = requests.get(case_url, headers={"accept":"application/json"}, params=args)
        else:
            args.update({"token":self.sa_token})
            if verb=="put":
                r = requests.put(case_url, headers={"accept":"application/json"}, params=args)
            else: 
                r = requests.post(case_url, headers={"accept":"application/json"}, params=args)
            
        success = not bool(r.json()["exit_code"])
        self.execution_log.update( 
            { datetime.now() : [path,success] } 
        )
        return r.json()
    
