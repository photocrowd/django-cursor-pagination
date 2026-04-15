from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    name="django-cursor-pagination",
    packages=["cursor_pagination"],
    package_data={"cursor_pagination": ["py.typed"]},
    version="0.3.0",
    description="Cursor based pagination for Django",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Photocrowd",
    author_email="devteam@photocrowd.com",
    url="https://github.com/photocrowd/django-cursor-pagination",
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.2",
        "Framework :: Django :: 6.0",
        "Typing :: Typed",
    ],
)
