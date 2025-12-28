"""Setup file for cursor-harness."""

from setuptools import setup, find_packages

setup(
    name="cursor-harness",
    version="3.0.2",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "anthropic>=0.39.0",
    ],
    entry_points={
        "console_scripts": [
            "cursor-harness=cursor_harness.cli:main",
        ],
    },
)

