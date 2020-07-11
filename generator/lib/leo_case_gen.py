import os


class LeoCaseGen:
    """
    Generates the Markdown documentation from the attack definitions
    """

    def __init__(self, config, env):
        self.config = config
        self.templates = {}
        self.templates["leo-cases"] = env.get_template("leo-cases.jinja2")

    def generate_leo_cases(self, definitions, outdir):
        """
        Generate the yaml config file for Leo
        """
        cases = []
        for case in definitions.case_set:
            if case["executors"]["leonidas_aws"]["implemented"]:
                cutcase = {}
                keylist = ["name", "input_arguments", "description", "category"]
                cutcase = {key: value for key, value in case.items() if key in keylist}
                cases.append(cutcase)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        with open(os.path.join(outdir, "caseconfig.yml"), "w") as outfile:
            outfile.write(
                self.templates["leo-cases"]
                .render({"cases": cases, "config": self.config})
                .replace("\n\n", "\n")
            )
