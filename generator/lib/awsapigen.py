"""
Code to generate the Leonidas API
"""

import os


class AWSAPIGen:
    """
    Generates the Flask API used to execute the attacker actions
    """

    def __init__(self, config, env):
        self.templates = {}
        self.env = env
        self.config = config
        self.templates["aws_python_function"] = env.get_template(
            "aws_python_execution_function.jinja2"
        )
        self.templates["api_core"] = env.get_template("python_api_core.jinja2")
        self.templates["serverless_config"] = env.get_template("serverless.jinja2")
        self.import_list = []
        self.casecount = 0

    def generate_python_api(self, outdir, definitions):
        """
        Generate the flask API that is deployed as a lambda function
        """
        for category in definitions.categories:
            self.import_list.append(category.replace(" ", "_").lower())
            self._generate_api_category(outdir, category, definitions)

        # API root file
        rendered = self.templates["api_core"].render({"categories": self.import_list})
        filename = os.path.join(outdir, "leonidas.py")
        with open(filename, "w") as apioutfile:
            apioutfile.write(rendered)

        # Serverless config
        filename = os.path.join(outdir, "serverless.yml")
        rendered = self.get_serverless_config(definitions)
        with open(filename, "w") as serverlessconfiguoutfile:
            serverlessconfiguoutfile.write(rendered)

    def _generate_api_category(self, outdir, category, definitions):
        """
        Build a given category of test cases
        """
        outdir = os.path.join(outdir, "api")
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        category_case_set = []
        for case in definitions.case_set:
            if case["category"] == category:
                try:
                    if case["executors"]["leonidas_aws"]["implemented"]:
                        category_case_set.append(case)
                        self.casecount = self.casecount + 1
                except KeyError:
                    continue
        rendered = self.templates["aws_python_function"].render(
            {
                "cases": category_case_set,
                "category": category.replace(" ", "_").lower(),
            }
        )
        py_filename = category.replace(" ", "_").lower() + ".py"
        filename = os.path.join(outdir, py_filename)
        pyoutfile = open(filename, "w")
        pyoutfile.write(rendered)
        pyoutfile.close()
        self.casecount = self.casecount

    def get_serverless_config(self, definitions):
        """
        Render the serverless.yml that Serverless uses as a configuration file
        """
        try:
            rendered = self.templates["serverless_config"].render(
                {
                    "permissions": sorted(list(definitions.permissions["aws"])),
                    "region": self.config["region"],
                    "resources": self.config["resources"],
                }
            )
        except KeyError:
            rendered = self.templates["serverless_config"].render(
                {
                    "permissions": sorted(list(definitions.permissions["aws"])),
                    "region": self.config["region"],
                    "resources": ['"*"'],
                }
            )
        return rendered
