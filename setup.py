import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="moneysplitter",
    version="0.0.1",
    author="Alexander Hildebrandt",
    author_email="alex@hilde.dev",
    description="Telegram bot to manage group purchases.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hildebro/moneysplitter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
