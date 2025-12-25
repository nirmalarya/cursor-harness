#!/usr/bin/env python3
"""
Setup script for cursor-harness package.
"""

from setuptools import setup, find_packages

setup(
    name="cursor-harness",
    version="2.3.0-dev",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "anthropic>=0.40.0",
    ],
    entry_points={
        "console_scripts": [
            "cursor-harness=cursor_harness.cursor_harness_cli:main",
        ],
    },
    python_requires=">=3.10",
)

