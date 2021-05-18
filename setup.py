import setuptools
from distutils.extension import Extension

packages = [package for package in setuptools.find_namespace_packages(where='mamoge', include='mamoge.*')]

packages = list(setuptools.find_packages(where="."))
print(packages)
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
    package_dir={"mamoge.taskplanner": "mamoge/taskplanner", "mamoge.taskplanner.test":"tests"},
    #packages=["mamoge.taskplanner", "mamoge.taskplanner.nx", "mamoge.taskplanner.optimize" ,"mamoge.taskplanner.tests"],
    packages=packages,
    python_requires=">=3.9"
)
