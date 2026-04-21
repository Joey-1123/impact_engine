from setuptools import setup, find_packages

setup(
    name="impact-engine",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "networkx",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "impact-engine=cli.main:main",
        ],
    },
)
