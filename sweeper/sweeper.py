#!/usr/bin/env python
# Author: Darko Poljak <darko.poljak@gmail.com>
# License: GPLv3

"""{0} {1}

Usage: {0} [options] [<directory>...]

Arguments:
    <directory> directory path to scan for files

Options:
-h, --help                                show this screen
-v, --version                             show version and exit
-b <blocksize>, --block-size=<blocksize>  size of block used when reading
                                          file's content [default: 4096]
-d <hashalgs>, --digest-algs=<hashalgs>   secure hash algorithm comma separated
                                          list [default: md5]
                                          note that multiple hashes will slow
                                          down sweeper
-a <action>, --action=<action>            action on duplicate files (pprint,
                                          print, remove, move)
                                          [default: pprint]
                                          -remove removes duplicate files
                                           except first or first with specified
                                           directory prefix found
                                          -move moves duplicate files to
                                           duplicates driectory, except first
                                           or first with specified directory
                                           prefix found
                                          -print prints result directory where
                                           keys are hash values and values are
                                           list of duplicate file paths
                                          -pprint prints sets of duplicate file
                                           paths each in it's line where sets
                                           are separated by blank newline
-m <directory>, --move=<directory>        move duplicate files to directory
                                          (used with move action)
                                          [default: ./dups]
-k <dirprefix>, --keep=<dirprefix>        directory prefix for remove and move
                                          actions
-s, --simulate                            if action is remove or move just
                                          simulate action by printing, do not
                                          actually perform the action
-V, --verbose                             print more info, note that verbosity
                                          will slow down sweeper due to text
                                          printing and additional information
                                          gathering
"""

from __future__ import print_function

__author__ = 'Darko Poljak <darko.poljak@gmail.com>'
__version__ = '0.4.1'
__license__ = 'GPLv3'

__all__ = [
    'file_dups', 'rm_file_dups', 'mv_file_dups', 'iter_file_dups'
]

import sys
import hashlib
import os
from collections import defaultdict
from functools import partial


# some differences in python versions
# we prefer iter methods
if sys.version_info[0] == 3:
    def _dict_iter_items(d):
        return d.items()

    def _dict_iter_keys(d):
        return d.keys()
else:
    def _dict_iter_items(d):
        return d.iteritems()

    def _dict_iter_keys(d):
        return d.iterkeys()


def _filehash(filepath, hashalg, block_size):
    """Calculate secure hash for given file content using
       specified hash algorithm. Use block_size block size
       when reading file content.
    """
    md = hashlib.new(hashalg)
    with open(filepath, "rb") as f:
        for buf in iter(lambda: f.read(block_size), b''):
            md.update(buf)
    return md.hexdigest()


def _uniq_list(list_):
    result = []
    for foo in list_:
        if foo not in result:
            result.append(foo)
    return result


def _gather_file_list(dirs):
    '''Gather file paths in directory list dirs.
       Return tuple (count, files) where count is files
       list length and files is list of file paths in
       specified directories.
    '''
    count = 0
    files = []
    for dir_ in dirs:
        for dirpath, dirnames, filenames in os.walk(dir_):
            count += len(filenames)
            files += [os.path.join(dirpath, fname) for fname in filenames]
    return (count, files)


# iter through file paths in files list
def _files_iter_from_list(files):
    for fpath in files:
        yield fpath


# iter through file paths by os.walking
def _files_iter_from_disk(topdirs):
    for topdir in topdirs:
        for dirpath, dirnames, filenames in os.walk(topdir):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                yield fpath


def file_dups(topdirs=['./'], hashalgs=['md5'], block_size=4096, verbose=False):
    """Find duplicate files in directory list. Return directory
       with keys equal to file hash value and value as list of
       file paths whose content is the same.
    """
    dups = defaultdict(list)
    if verbose:
        print('gathering and counting files...', end='')
        sys.stdout.flush()
        count, files = _gather_file_list(topdirs)
        current = 1
        print(count)
        _files_iter = partial(_files_iter_from_list, files)
    else:
        _files_iter = partial(_files_iter_from_disk, topdirs)

    for fpath in _files_iter():
        if verbose:
            print('\rprocessing file {0}/{1}'.format(current, count),
                  end='')
            sys.stdout.flush()
            current += 1
        hexmds = [_filehash(fpath, h, block_size) for h in hashalgs]
        hexmd = tuple(hexmds)
        dups[hexmd].append(fpath)

    if verbose:
        print('')
    result = {}
    for k, v in _dict_iter_items(dups):
        uniq_v = _uniq_list(v)
        if len(uniq_v) > 1:
            result[k] = uniq_v
    return result


def _extract_files_for_action(topdirs, hashalgs, block_size, keep_prefix,
                              verbose):
    for files in iter_file_dups(topdirs=topdirs, hashalgs=hashalgs,
                                block_size=block_size, verbose=verbose):
        found = False
        if keep_prefix:
            result = []
            for f in files:
                if f.startswith(keep_prefix) and not found:
                    found = True
                else:
                    result.append(f)
        if not found:
            result = files[1:]
        yield (files, result)


def rm_file_dups(topdirs=['./'], hashalgs=['md5'], block_size=4096,
                 simulate=False, keep_prefix=None, verbose=False):
    """Remove duplicate files found in specified directory list.
       If keep_prefix is specified then first file with that path
       prefix found is kept in the original directory.
       Otherwise first file in list is kept in the original directory.
       If simulate is True then only print the action, do not actually
       perform it.
    """
    for dups, extracted in _extract_files_for_action(topdirs, hashalgs,
                                                     block_size, keep_prefix,
                                                     verbose):
        if simulate or verbose:
            print('found duplicates: \n{}'.format(dups))
        for f in extracted:
            if simulate or verbose:
                print('rm {}'.format(f))
            if not simulate:
                os.remove(f)


def mv_file_dups(topdirs=['./'], hashalgs=['md5'], block_size=4096,
                 dest_dir='dups', simulate=False, keep_prefix=None,
                 verbose=False):
    """Move duplicate files found in specified directory list.
       If keep_prefix is specified then first file with that path
       prefix found is kept in the original directory.
       Otherwise first file in list is kept in the original directory.
       If simulate is True then only print the action, do not actually
       perform it.
    """
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
    if not os.path.isdir(dest_dir):
        raise OSError('{} is not a directory'.format(dest_dir))
    import shutil
    for dups, extracted in _extract_files_for_action(topdirs, hashalgs,
                                                     block_size, keep_prefix,
                                                     verbose):
        if simulate or verbose:
            print('found duplicates: \n{}'.format(dups))
        for f in extracted:
            if simulate or verbose:
                print('mv {0} to {1}'.format(f, dest_dir))
            if not simulate:
                shutil.move(f, dest_dir)


def iter_file_dups(topdirs=['./'], rethash=False, hashalgs=['md5'],
                   block_size=4096, verbose=False):
    """Yield duplicate files when found in specified directory list.
       If rethash is True then tuple hash value and duplicate paths list is
       returned, otherwise duplicate paths list is returned.
    """
    dups = file_dups(topdirs, hashalgs, block_size, verbose)
    for hash_, fpaths in _dict_iter_items(dups):
        if rethash:
            yield (hash_, fpaths)
        else:
            yield fpaths


def _remap_keys_to_str(d):
    '''Iterator that remaps dictionary keys to string in case keys are tuple
       or list. Leave it unchanged otherwise.
    '''
    for k in _dict_iter_keys(d):
        if isinstance(k, tuple) or isinstance(k, list):
            key = ','.join(k)
        else:
            key = k
        yield (key, d[k])


def main():
    """Main when used as script. See usage (--help).
    """
    import json
    from docopt import docopt

    args = docopt(__doc__.format(sys.argv[0], __version__),
                  version=" ".join(('sweeper', __version__)))

    topdirs = args['<directory>']
    if not topdirs:
        topdirs = ['./']

    action = args['--action']
    verbose = args['--verbose']

    # set block size as int
    try:
        bs = int(args['--block-size'])
        args['--block-size'] = bs
    except ValueError:
        print('Invalid block size "{}"'.format(args['--block-size']))
        sys.exit(1)
    hashalgs = args['--digest-algs'].split(',')
    hashalgs_uniq = _uniq_list(hashalgs)
    if len(hashalgs) != len(hashalgs_uniq):
        print('Duplicate hash algorithms specified')
        sys.exit(1)
    block_size = args['--block-size']
    simulate = args['--simulate']
    keep_prefix = args['--keep']
    dest_dir = args['--move']

    if action == 'print' or action == 'pprint':
        dups = file_dups(topdirs=topdirs,
                         hashalgs=hashalgs,
                         block_size=block_size,
                         verbose=verbose)
        # defaultdict(list) -> dict
        spam = dict(dups)
        if spam:
            if action == 'pprint':
                for _, fpaths in _dict_iter_items(spam):
                    for path in fpaths:
                        print(path)
                    if fpaths:
                        print('')
            else:
                print(json.dumps({k: v for k, v in _remap_keys_to_str(spam)},
                                 indent=4))
    elif action == 'move':
        mv_file_dups(topdirs=topdirs, hashalgs=hashalgs,
                     block_size=block_size,
                     dest_dir=dest_dir,
                     simulate=simulate,
                     keep_prefix=keep_prefix,
                     verbose=verbose)
    elif action == 'remove':
        rm_file_dups(topdirs=topdirs, hashalgs=hashalgs,
                     block_size=block_size,
                     simulate=simulate,
                     keep_prefix=-keep_prefix,
                     verbose=verbose)
    else:
        print('Invalid action "{}"'.format(action))


if __name__ == '__main__':
    main()
