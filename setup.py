import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bottle-users-jefmud", # Replace with your own username
    version="0.0.1",
    author="Jeffrey Muday",
    author_email="jeff@mudaylab.com",
    description="A simple package for Bottle user authentication and sessions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jefmud/bottle_users",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
)
