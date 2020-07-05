import unittest
import jinja2
import os
import yaml

from lib.definitions import Definitions


class TestDefinitionIngestion(unittest.TestCase):
    def setUp(self):
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(os.path.join(".", "templates")),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        self.config = {"definitions_path": "./definitions", "output_dir": "./output"}
        self.basic_casefile = False
        self.notimplemented_casefile = None

    def test_single_case_ingestion(self):
        """
        Test whether a basic definition with a single case in it loads properly
        """
        filedata = yaml.safe_load(
            open(os.path.join("test", "test_defs", "basic.yml"), "r")
        )
        definitions = Definitions(self.config, self.env)
        definitions._generate_definitions(filedata)
        self.assertEqual(len(definitions.categories), 1, "Should only be one category")
        self.assertEqual(
            "Discovery" in definitions.categories,
            True,
            "Should be in the Discovery category",
        )
        self.assertEqual(len(definitions.case_set), 1, "Should be a single case")


if __name__ == "__main__":
    unittest.main()
