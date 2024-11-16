"""
Code to generate the Leonidas API to be used within Kubernetes
"""

import os


class KubeAPIGen:
    """
    Generates the Flask API & Kubernetes resources 
    """

    def __init__(self, config, env):
        self.templates = {}
        self.env = env
        self.config = config
        if "namespace" not in config or config["namespace"] == "":
            self.config["namespace"] = "default"
        
        self.templates["kube_python_function"] = env.get_template(
            "kube_python_execution_function.jinja2"
        )
        self.templates["api_core"] = env.get_template("python_api_core.jinja2")
        self.templates["serverless_config"] = env.get_template("serverless.jinja2")
        self.templates["kube_resources"] = env.get_template("kube-resources.jinja2")
        self.import_list = []
        self.casecount = 0

    
    def generate_kube_resources(self, is_namespaced):
        """
        Generate the Kubernetes resources for Leonidas
        """
        return self.templates["kube_resources"].render(
            {
                "namespace":    self.config["namespace"],
                "is_namespaced":is_namespaced,
                "image_url":    self.config["image_url"],
            }
        )

    def generate_python_api(self, outdir, definitions):
        """
        Generate the flask API 
        """
        for category in definitions.categories:
            self.import_list.append(category.replace(" ", "_").lower())
            self._generate_api_category(outdir, category, definitions)

        # API root file
        rendered = self.templates["api_core"].render({"categories": self.import_list})
        filename = os.path.join(outdir, "leonidas.py")
        with open(filename, "w") as apioutfile:
            apioutfile.write(rendered)


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
                    if case["executors"]["leonidas_kube"]["implemented"]:
                        category_case_set.append(case)
                        self.casecount = self.casecount + 1
                except KeyError:
                    continue
        rendered = self.templates["kube_python_function"].render(
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

