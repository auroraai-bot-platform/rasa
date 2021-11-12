from setuptools import setup, find_packages

setup(
    name="rasa_addons",
    version="2.4.3-bf.1",
    author="Botfront",
    description="Rasa Addons - Components for Rasa and Botfront",
    install_requires=[
        "fuzzy_matcher",
    ],
    packages=find_packages(),
    licence="Apache 2.0",
    url="https://botfront.io",
    author_email="hi@botfront.io",
)
