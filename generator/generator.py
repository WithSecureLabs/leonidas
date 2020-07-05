#!/usr/bin/env python

import json
import os
from pathlib import Path

import jinja2
import typer
import yaml

from lib.definitions import Definitions
from lib.awsapigen import AWSAPIGen
from lib.docgen import DocGen
from lib.leo_case_gen import LeoCaseGen
from lib.sigmaexport import SigmaExport


def debug(text):
    print(text)
    return ""


env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(".", "templates")),
    autoescape=jinja2.select_autoescape(["html", "xml"]),
)

env.filters["debug"] = debug


class Generator:
    def initialise(self, config, env):
        self.config = config
        self.definitions = Definitions(self.config, env)
        self.docgen = DocGen(self.config, env)
        self.awsapigen = AWSAPIGen(self.config, env)
        self.leocasegen = LeoCaseGen(self.config, env)
        self.sigmaexport = SigmaExport(self.config, env)


app = typer.Typer()
generator = Generator()


@app.callback()
def main(
    config: Path = typer.Option(
        "config.yml", help="Path to config file", show_default=True
    )
):
    config = yaml.safe_load(open(config, "r").read())
    if not os.path.exists(config["output_dir"]):
        os.makedirs(config["output_dir"])
    generator.initialise(config, env)


@app.command()
def definitions():
    """
    Pretty-print definitions dictionary
    """
    print(json.dumps(generator.definitions.case_set, indent=4))


@app.command()
def validate():
    """
    Validate the test definitions
    """
    if not generator.definitions.validate():
        print("Validation failed")
        raise typer.Exit(code=1)
    else:
        print(
            "Validation successful - validated {} cases".format(
                generator.definitions.casecount
            )
        )


@app.command()
def generate_aws_api():
    """
    Generate the AWS Leonidas API
    """
    print("Generating API")
    generator.definitions.construct_definitions()
    PYOUTPUTDIR = "leonidas"
    outdir = os.path.join(generator.config["output_dir"], PYOUTPUTDIR)
    generator.awsapigen.generate_python_api(outdir, generator.definitions)
    print(
        "API generation complete - {} cases generated".format(
            generator.awsapigen.casecount
        )
    )


@app.command()
def docs():
    """
    Generate the leonidas documentation (http://detectioninthe.cloud)
    """
    print("Generating Docs")
    generator.definitions.construct_definitions()
    MARKDOWNOUTPUTDIR = "docs"
    outdir = os.path.join(generator.config["output_dir"], MARKDOWNOUTPUTDIR)
    generator.docgen.generate_markdown(outdir, generator.definitions)


@app.command()
def iam_policy():
    """
    Print the AWS IAM policy necessary to execute all the AWS test cases
    """
    generator.definitions.construct_definitions()
    print(generator.definitions.get_aws_policy())


@app.command()
def serverless_config():
    """
    Print the Serverless framework configuration 
    used to deploy the Leonidas API to AWS
    """
    generator.definitions.construct_definitions()
    print(generator.awsapigen.get_serverless_config(generator.definitions))


@app.command()
def leo():
    """
    Generate the configuration file for Leo, the CLI tool 
    for executing test cases against an instance of Leonidas
    """
    print("Generating Leo Case Configuration")
    generator.definitions.construct_definitions()
    LEOCASEOUTPUTDIR = "caseconfig"
    outdir = os.path.join(generator.config["output_dir"], LEOCASEOUTPUTDIR)
    generator.leocasegen.generate_leo_cases(generator.definitions, outdir)


@app.command()
def sigma():
    """
    Generate the Sigma rule definitions
    """
    print("Generating Sigma rules")
    generator.definitions.construct_definitions()
    SIGMAOUTPUTDIR = "sigma"
    outdir = os.path.join(generator.config["output_dir"], SIGMAOUTPUTDIR)
    generator.sigmaexport.export_sigma(generator.definitions, outdir)


if __name__ == "__main__":
    app()
