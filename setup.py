from setuptools import setup

TEST_DEPENDENCIES = [
    "black==19.10b0",
    "flake8==3.7.9",
    "pytest==5.4.1",
    "pytest-cov==2.8.1",
]

setup(
    name="pytojsonschema",
    description="A package to convert Python type annotations into JSON schemas",
    version="1.0.0",
    author="Osirium",
    author_email="support@osirium.com",
    maintainer="Carlos Ruiz Lantero",
    maintainer_email="carlos.ruiz.lantero@osirium.com",
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
