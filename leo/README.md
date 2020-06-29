## Leo - Test Case Orchestrator

Leo is a helper script designed to make it easier to execute killchains as a whole, as opposed to individual test cases. To execute a suite of test cases in Leonidas in an automated fashion. To set Leo up, run the following:

* `pip install poetry`
* `cd ./leo`
* `poetry install`

To generate the config file for Leo:

* `cd generator && poetry run python generator.py leo` to generate the test case definitions for Leo
* `cp ./output/caseconfig/caseconfig.yml ./leo`
* edit the `caseconfig.yml` file in `./leo` to set the URL, API gateway API key, and to modify/reorder/remove test cases as required

To execute the cases you've configured:

* `poetry run ./leo.py caseconfig.yml`