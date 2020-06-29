"""
Code for generating the markdown used to build the documentation
"""


import os
from collections import defaultdict
import jinja2


class DocGen:
    """
    Generates the Markdown documentation from the attack definitions
    """

    def __init__(self, config, env):
        self.templates = {}
        self.config = config
        self.templates["lucene"] = env.get_template("lucene-query.jinja2")
        self.templates["markdown"] = env.get_template("markdown.jinja2")

    def _generate_markdown(self, case):
        """
        Generates markdown for a given case
        """
        # Lucene query generation
        lucene_dict = {
            "sources": case["detection"]["sources"],
            "data": case["input_arguments"],
        }
        case["lucene_query"] = self.templates["lucene"].render(lucene_dict)
        # AWS CLI command generation
        command_template = jinja2.Template(case["executors"]["sh"]["code"])
        if case["input_arguments"]:
            aws_cli_render_args = {}
            for arg in case["input_arguments"]:
                aws_cli_render_args[arg] = case["input_arguments"][arg]["value"]
            case["compiled_command"] = command_template.render(aws_cli_render_args)
        else:
            case["compiled_command"] = command_template.render()

        render_dict = {"case": case}
        return self.templates["markdown"].render(render_dict)

    def generate_markdown(self, outdir, definitions):
        """
        Generates markdown for the definitions ingested
        """
        doc_cases = defaultdict(lambda: defaultdict(list))

        if not os.path.exists(outdir):
            os.makedirs(outdir)
        for category in definitions.categories:
            cat_outdir = os.path.join(outdir, category.replace(" ", "_").lower())
            if not os.path.exists(cat_outdir):
                os.makedirs(cat_outdir)

            for case in definitions.case_set:
                if case["category"] == category:
                    doc_cases[category][case["name"]] = case

            for technique in doc_cases[category]:
                rendered = self._generate_markdown(doc_cases[category][technique])
                md_filename = technique.replace(" ", "_").lower() + ".md"
                filename = os.path.join(cat_outdir, md_filename)
                mdoutfile = open(filename, "w")
                mdoutfile.write(rendered)
                mdoutfile.close()
