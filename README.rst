sweeper
=======

Find duplicate files and perform action.

Usage
=====

Print duplicates

.. code:: python

    from sweeper import file_dups
    dups = file_dups(['images1', 'images2'])
    print(dups)

Remove duplicate files

.. code:: python

    from sweeper import rm_file_dups
    rm_file_dups(['images'])

Perform custom action

.. code:: python

    from sweeper import iter_file_dups
    for files in iter_file_dups(['images']):
        for fname in files:
            print('found duplicate file with name: %s' % fname)

As script::

    python sweeper.py --help

As installed console script::
    
    sweeper --help

Installation
============

from source::

    python setup.py install

or from PyPI::

    pip install sweeper

Documentation
=============

this README.rst, code itself, docstrings

sweeper can be found on github.com at:

https://github.com/darko-poljak/sweeper

Tested With
===========

Python2.7.6, Python3.3.3

