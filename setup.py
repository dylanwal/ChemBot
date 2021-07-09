from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='chembot',
    version='0.0.1',
    url='',
    license='MIT License',
    author='Dylan Walsh',
    author_email='dylanwal@mit.edu',
    description='ChemBot: Tools for automating chemistry.',
    classifiers=[
                  "Programming Language :: Python :: 3",
                  "License :: OSI Approved :: MIT License",
                  "Operating System :: OS Independent",
              ],
    package_dir={"": "main_code"},
    packages=find_packages(where="main_code")
)
