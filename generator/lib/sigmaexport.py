"""
Code for generating the markdown used to build the documentation
"""


import os
from collections import defaultdict


class SigmaExport:
    """
    Generates the Markdown documentation from the attack definitions
    """

    def __init__(self, config, env):
        self.templates = {}
        self.config = config
        self.env = env

    def export_sigma(self, definitions, outdir):
        sigma_cases = defaultdict(lambda: defaultdict(list))
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        for category in definitions.categories:
            cat_outdir = os.path.join(outdir, category.replace(" ", "_").lower())
            if not os.path.exists(cat_outdir):
                os.makedirs(cat_outdir)

            for case in definitions.case_set:
                if case["category"] == category:
                    sigma_cases[category][case["name"]] = case

            for technique in sigma_cases[category]:
                sigma_filename = technique.replace(" ", "_").lower() + ".yaml"
                filename = os.path.join(cat_outdir, sigma_filename)
                with open(filename, "w") as sigmaoutfile:
                    sigmaoutfile.write(sigma_cases[category][technique]["sigma"])
        print("Generated {} sigma definitions".format(len(definitions.case_set)))
