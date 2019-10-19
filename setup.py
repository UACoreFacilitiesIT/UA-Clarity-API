import os
from setuptools import setup, find_packages


def readme(filename):
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with open(full_path, 'r') as file:
        return file.read()


setup(
    name="ua_clarity_api",
    version="1.0.3",
    packages=find_packages(),
    author="Stephen Stern, Rafael Lopez",
    author_email="sterns1@email.arizona.edu",
    include_package_data=True,
    description=(
        "API that interacts with Illumina Clarity LIMS REST architecture."),
    long_description=readme("README.md"),
    long_description_content_type='text/markdown',
    url="https://github.com/UACoreFacilitiesIT/UA-Clarity-API",
    license="MIT",
    project_urls={
        "Clarity REST Documentation": "https://www.genologics.com/developer/"}
)
