#!/usr/bin/env python
# Author: Darko Poljak <darko.poljak@gmail.com>
# License: GPLv3

"""Sweeper.

Usage: sweeper.py [options] [<directory>...]

Arguments:
    <directory> directory path to scan for files

Options:
-h, --help                                show this screen
-b <blocksize>, --block-size=<blocksize>  size of block used when reading
                                          file's content [default: 4096]
-d <hashalg>, --digest-alg=<hashalg>      secure hash algorithm [default: md5]
-a <action>, --action=<action>            action on duplicate files (pprint,
                                          print, remove, move)
                                          [default: pprint]
                                          -remove removes duplicate files
                                           except first found
                                          -move moves duplicate files to
                                           duplicates driectory, except first
                                           found
                                          -print prints result directory where
                                           keys are hash values and values are
                                           list of duplicate file paths
                                          -pprint prints sets of duplicate file
                                           paths each in it's line where sets
                                           are separated by blank newline
-m <directory>, --move=<directory>        move duplicate files to directory
                                          (used with move action)
                                          [default: ./dups]
"""

__author__ = 'Darko Poljak <darko.poljak@gmail.com>'
__version__ = '0.3.0'
__license__ = 'GPLv3'

__all__ = [
    'file_dups', 'rm_file_dups', 'mv_file_dups', 'iter_file_dups'
]

import sys
import hashlib
import os
from collections import defaultdict


# some differences in python versions
if sys.version_info[0] == 3:
    def _do_encode(buf):
        return buf

    def _dict_iter_items(d):
        return d.items()
else:
    def _do_encode(buf):
        return buf

    def _dict_iter_items(d):
        return d.iteritems()


def _filehash(filepath, hashalg, block_size):
    """Calculate secure hash for given file content using
       specified hash algorithm. Use block_size block size
       when reading file content.
    """
    md = hashlib.new(hashalg)
    with open(filepath, "rb") as f:
        for buf in iter(lambda: f.read(block_size), b''):
            md.update(_do_encode(buf))
    return md.hexdigest()


def file_dups(topdirs=['./'], hashalg='md5', block_size=4096):
    """Find duplicate files in directory list. Return directory
       with keys equal to file hash value and value as list of
       file paths whose content is the same.
    """
    dups = defaultdict(list)
    for topdir in topdirs:
        for dirpath, dirnames, filenames in os.walk(topdir):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                hexmd = _filehash(fpath, hashalg, block_size)
                dups[hexmd].append(fpath)
    result = {k: v for k, v in _dict_iter_items(dups) if len(v) > 1}
    return result


def rm_file_dups(topdirs=['./'], hashalg='md5', block_size=4096):
    """Remove duplicate files found in specified directory list.
       First file in list is kept.
    """
    for files in do_with_file_dups(topdirs, hashalg, block_size):
        for f in files:
            os.remove(f)


def mv_file_dups(topdirs=['./'], hashalg='md5', block_size=4096,
                 dest_dir='dups'):
    """Move duplicate files found in specified directory list.
       First file in list is kept in the original directory.
    """
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    if not os.path.isdir(dest_dir):
        raise OSError('%s is not a directory' % dest_dir)
    import shutil
    for files in do_with_file_dups(topdirs, hashalg, block_size):
        for i, f in enumerate(files):
            if i > 0:
                shutil.move(f, dest_dir)


def iter_file_dups(topdirs=['./'], rethash=False, hashalg='md5',
                   block_size=4096):
    """Yield duplicate files when found in specified directory list.
       If rethash is True then tuple hash value and duplicate paths list is
       returned, otherwise duplicate paths list is returned.
    """
    dups = file_dups(topdirs, hashalg, block_size)
    for hash_, fpaths in _dict_iter_items(dups):
        if rethash:
            yield (hash_, fpaths)
        else:
            yield fpaths


def main():
    """Main when used as script. See usage (--help).
    """
    import json
    from docopt import docopt

    args = docopt(__doc__)

    topdirs = args['<directory>']
    if not topdirs:
        topdirs = ['./']

    action = args['--action']
    try:
        bs = int(args['--block-size'])
        args['--block-size'] = bs
    except ValueError:
        print('Invalid block size "%s"' % args['--block-size'])
        sys.exit(1)

    if action == 'print' or action == 'pprint':
        dups = file_dups(topdirs, args['--digest-alg'], args['--block-size'])
        spam = dict(dups)
        if spam:
            if action == 'pprint':
                for h, fpaths in _dict_iter_items(spam):
                    for path in fpaths:
                        print(path)
                    print('')
            else:
                print(json.dumps(spam, indent=4))
    elif action == 'move':
        mv_file_dups(topdirs, args['--digest-alg'], args['--block-size'],
                     args['--move'])
    elif action == 'remove':
        rm_file_dups(topdirs, args['--digest-alg'], args['--block-size'])
    else:
        print('Invalid action "%s"' % action)


# if used as script call main function
if __name__ == '__main__':
    main()
