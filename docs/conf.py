from pathlib import Path
import yaml
config = yaml.safe_load((Path(__file__).resolve().parents[1] / "setup.yml").read_text())
project = config["name"]
author = config["author"]
copyright = config["copyright"]
version = release = config["version"]
extensions = ["myst_parser"]
exclude_patterns = ["_build"]
html_theme = "alabaster"
