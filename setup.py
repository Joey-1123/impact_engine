# Copyright (c) 2025 Shubham Panchal (Joey). MIT License.
import re
from pathlib import Path
from setuptools import setup, find_packages


def read_version():
    version_file = Path(__file__).parent / "core" / "version.py"
    match = re.search(
        r'__version__\s*=\s*["\']([^"\']+)["\']',
        version_file.read_text(encoding="utf-8"),
    )
    if match:
        return match.group(1)
    raise RuntimeError("Unable to find __version__ in core/version.py")


setup(
    name="impact-engine",
    version=read_version(),
    description="Python static impact analysis for codebases",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "networkx>=3.6.1",
        "pathspec>=0.12.0",
    ],
    extras_require={
        "terminal": [
            "rich>=15.0.0",
        ],
        "web": [
            "Django>=5.0",
            "djangorestframework>=3.14.0",
            "django-extensions>=3.2.1",
            "python-dotenv>=1.2.2",
            "requests>=2.32.0",
        ],
        "visual": [
            "graphviz>=0.21",
        ],
        "watch": [
            "watchdog>=6.0.0",
        ],
        "full": [
            "rich>=15.0.0",
            "Django>=5.0",
            "djangorestframework>=3.14.0",
            "django-extensions>=3.2.1",
            "python-dotenv>=1.2.2",
            "requests>=2.32.0",
            "graphviz>=0.21",
            "watchdog>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "impact-engine=cli.main:main",
        ],
    },
)
