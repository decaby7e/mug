import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as req:
    requirements = req.read().splitlines()

setuptools.setup(
    name="mug",
    version="0.0.1",
    author="Jack Polk",
    author_email="mug@ranvier.net",
    description="CUPS print accounting plugin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: GPLv3 License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "mug = mug.cli.__main__:app",
        ],
    },
    install_requires=requirements,
)
