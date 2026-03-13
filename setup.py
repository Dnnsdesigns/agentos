from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentos",
    version="0.1.0",
    author="AgentOS Contributors",
    description="A lightweight framework for building and managing autonomous AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dnnsdesigns/agentos",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    keywords="agents ai framework task-management",
    project_urls={
        "Bug Reports": "https://github.com/dnnsdesigns/agentos/issues",
        "Source": "https://github.com/dnnsdesigns/agentos",
    },
    package_data={
        "agentos": ["py.typed"],
    },
)
