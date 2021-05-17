import setuptools


setuptools.setup(
    name="mamoge-taskplanner",
    version="0.0.1",
    author="matthias fueller",
    author_email="matthias.fueller@fhdw.de",
    description="mamoge task planner",
    long_description="TBD",
    long_description_content_type="text/markdown",
    url="https://github.com/TBD",
    project_urls={
        "Bug Tracker": "https://github.com/TBD",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
)
