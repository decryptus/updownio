.PHONY: test build docs check
PYTHON ?= python3
test:
	$(PYTHON) -m unittest discover -s tests -v
build:
	$(PYTHON) -m build
docs:
	$(PYTHON) -m sphinx -W --keep-going -b html docs docs/_build/html
check: test build docs
	$(PYTHON) -m twine check --strict dist/*
