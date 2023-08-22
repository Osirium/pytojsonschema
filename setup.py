import os
from setuptools import setup

TEST_DEPENDENCIES = [
    "black==23.7.0",
    "flake8==3.7.9",
    "pytest==7.4.0",
    "pytest-cov==4.1.0",
]

with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), "README.md"), encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name="pytojsonschema",
    description="A package to convert Python type annotations into JSON schemas",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    version="2.0.0-dev6",
    author="Osirium",
    author_email="support@osirium.com",
    maintainer="Carlos Ruiz Lantero",
    maintainer_email="carlos.ruiz.lantero@gmail.com",
    url="https://github.com/Osirium/pytojsonschema",
    packages=["pytojsonschema"],
    classifiers=[
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    tests_require=TEST_DEPENDENCIES,
    extras_require={"test": TEST_DEPENDENCIES},
)
