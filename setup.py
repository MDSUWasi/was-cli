"""
Setup script for WAS CLI.
All package metadata lives here for maximum compatibility
with both old and modern pip/setuptools versions.
"""
import os
from setuptools import setup, find_packages

# Safely read README — don't crash if it's missing
here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, "README.md")
try:
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "A document time machine CLI — version control for personal documents and study notes."

setup(
    name="was-cli",
    version="1.4.0",
    description="A document time machine CLI — version control for personal documents and study notes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    python_requires=">=3.6",
    packages=find_packages(include=["was*"]),
    entry_points={
        "console_scripts": [
            "was = was.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
)