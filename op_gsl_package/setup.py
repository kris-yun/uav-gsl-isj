from setuptools import setup, find_packages

setup(
    name="op-gsl",
    version="0.1.0",
    description="Orienteering-based Gas Source Localization",
    author="ZYC",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.20",
    ],
)
