from setuptools import setup

setup(
    name='2done',
    version='1.0',
    py_modules=['2done'],
    install_requires=[
        'Click',
        'terminaltables',
        'colorama',
    ],
    entry_points='''
        [console_scripts]
        2=2done:cli
    ''',
)
