from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / "README.md").read_text(encoding="utf-8")


setup(
    name="web application racing results analysis",
    version="1.0",
    description="""The website provides three pages:
- at http://localhost:5000/report shows general statistics
- http://localhost:5000/report/drivers/ shows a list of driver names and codes. The code is a link to driver information.
- http://localhost:5000/report/drivers/?driver_id=SVF shows driver information.
In addition, each route can receive an order parameter
http://localhost:5000/report/drivers/?order=desc""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.foxminded.ua/foxstudent104883/task_7_flask.git",
    author="Dmitro Bobrow",
    author_email="dmitr.bobrow2012@gmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3 :: Only",
        "Flask :: 3.0.2",
        "Flask-Caching :: 2.1.0",
        "Flask-Testing :: 0.8.1",
        "Jinja2 :: 3.1.3"
    ],
    install_requires=[
        "Flask == 3.0.2",
        "Flask-Caching == 2.1.0",
        "Flask-Testing == 0.8.1",
        "Jinja2 == 3.1.3",
        "beautifulsoup4 == 4.12.3",
        "flasgger == 0.9.7.1",
        "jsonschema == 4.22.0",
        "peewee == 3.17.5",
        "pytest == 8.2.2",
        'lxml==4.9.3'
    ],
    entry_points={
        'console_scripts': [
            'task_7_flask = main:__main__'
        ]
    },
    keywords="sample, setuptools, development",
    package_dir={
        "": "src"},
    packages=find_packages(
        where="src"),
    python_requires=">=3.7, <4",
    extras_require={
                    "dev": ["check-manifest"],
                    "test": ["coverage"],
    },
    package_data={
        "files": ["data/*"],
    },
    project_urls={
        "Source": "https://git.foxminded.ua/foxstudent104883/task_7_flask",
    },
)
