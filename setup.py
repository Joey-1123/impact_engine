from pathlib import Path
from setuptools import setup, find_packages


def read_version():
    namespace = {}
    version_file = Path(__file__).parent / "core" / "version.py"
    exec(version_file.read_text(encoding="utf-8"), namespace)
    return namespace["__version__"]


setup(
    name="impact-engine",
    version=read_version(),
    description="Static impact analysis for Python codebases",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "networkx>=3.6.1",
        "rich>=15.0.0",
        "requests>=2.0.0",
    ],
    extras_require={
        "web": [
            "Django>=5.0",
            "djangorestframework>=3.14.0",
            "django-extensions>=3.2.1",
            "python-dotenv>=1.2.2",
        ],
        "visual": [
            "graphviz>=0.21",
        ]
    },
    entry_points={
        "console_scripts": [
            "impact-engine=cli.main:main",
        ],
    },
)
