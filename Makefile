netlifydocs:
	pip3 install poetry
	cd generator && poetry install && poetry run ./generator.py docs
	pip install mkdocs mkdocs-material
	cd output && mkdocs build
