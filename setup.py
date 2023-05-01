"""setup.py file for imageassessmentservice."""

from pathlib import Path
from typing import List
from setuptools import setup, find_packages


def read_requirements() -> List[str]:
    with open("requirements.txt", "r") as file:
        requirements = [line.rstrip("\n") for line in file.readlines()]

    return requirements


setup(
    name="imageassessmentservice",
    version="0.0.1",
    author="ae137",
    author_email="a_e_mailings@posteo.de",
    packages=find_packages(
        include=["imageassessmentservice", "imageassessmentservice.*"]
    ),
    url="https://github.com/ae137/ImageAssessmentService",
    license="GPL v3",
    description="A package providing a service and a client for assessing images",
    long_description=Path("README.md").read_text(),
    long_description_content_type="text/markdown",
    requires=["setuptools", "grpc_tools"],
    install_requires=read_requirements(),
    setup_requires=["pytest-runner", "flake8"],
    tests_require=["pytest"],
    python_requires=">=3.8",
)
