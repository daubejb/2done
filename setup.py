from setuptools import setup, find_packages
import os

setup(
        name='2done',
        version='1.0',
        author='Jeffrey B. Daube',
        author_email='daubejb@gmail.com',
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        url="http://www.github.com/daubejb/2done",
        description='todo app to manage todo list from terminal with \
                data residing on a google sheet',
        keywords='todo to do list application 2done daube design \
                daubedesign',
        install_requires = [
            'terminaltables',
            'prompt_toolkit',
            ],
        entry_points = {
            'console_scripts': [
                '2=2done.2done:main',
                ],
            },
        )
