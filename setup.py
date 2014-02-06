import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


import sweeper.sweeper as sw


setup(
    name='sweeper',
    version=sw.__version__,
    author='Darko Poljak',
    author_email='darko.poljak@gmail.com',
    description='Find duplicate files and perform action.',
    license="GPLv3",
    keywords=['find duplicate files', ],
    url='https://github.com/darko-poljak/sweeper',
    download_url='https://github.com/darko-poljak/sweeper',
    packages=['sweeper'],
    entry_points={
        'console_scripts': [
            'sweeper=sweeper.sweeper:main',
        ],
    },
    long_description=read('README.rst'),
    platforms="OS Independent",
    install_requires=["docopt"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
