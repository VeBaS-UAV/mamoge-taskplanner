"""Setup configuration of the project."""
import setuptools

setuptools.setup(
    name="mamoge-taskplanner",
    version="0.0.1",
    author="matthias fueller, pascal niggemeier",
    author_email="matthias.fueller@fhdw.de, pascal.niggemeier@fhdw.de",
    description="mamoge task planner",
    long_description="""MamoGe Taskplanner is a package that is a colletion of service
    templates and designs for delivering dynamic and robust task allocation and
    management.""",
    long_description_content_type="text/markdown",
    url="https://github.com/TBD",
    project_urls={"Bug Tracker": "https://github.com/MamoGe/mamoge-taskplanner/issues"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.9",
)
