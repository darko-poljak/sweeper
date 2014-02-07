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
-V, --verbose                             print more info
                                          note that verbosity will slow down
                                          sweeper due to text printing and
                                          gathering additional information
-S, --safe-mode                           enable safe mode: compare hash
                                          duplicate files byte by byte too
                                          note that it will further slow down
                                          sweeper but will overcome hash
                                          collisions (although this is
                                          unlikely)
"""

from __future__ import print_function

__author__ = 'Darko Poljak <darko.poljak@gmail.com>'
__version__ = '0.5.0'
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

    def _dict_iter_values(d):
        return d.values()
else:
    def _dict_iter_items(d):
        return d.iteritems()

    def _dict_iter_keys(d):
        return d.iterkeys()

    def _dict_iter_values(d):
        return d.itervalues()

    range = xrange


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
            # replace fpath with realpath value (eliminate symbolic links)
            files += [os.path.realpath(os.path.join(dirpath, fname))
                      for fname in filenames]
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
                # replace fpath with realpath value (eliminate symbolic links)
                fpath = os.path.realpath(os.path.join(dirpath, fname))
                yield fpath


def _fbequal(fpath1, fpath2):
    '''Compare files byte by byte. If files are equal return True,
       False otherwise.
       fpath1 and fpath2 are file paths.
    '''
    with open(fpath1, "rb") as f1, open(fpath2, "rb") as f2:
        while True:
            b1 = f1.read(1)
            b2 = f2.read(1)
            if b1 != b2:  # different bytes
                return False
            if not b1 or not b2:  # end in one or both files
                break
    if not b1 and not b2:  # end in both files, files are equal
        return True
    # end in one file but not in the other, files aren't equal
    return False


def file_dups(topdirs=['./'], hashalgs=['md5'], block_size=4096, verbose=False,
              safe_mode=False):
    """Find duplicate files in directory list. Return directory
       with keys equal to file hash value and value as list of
       file paths whose content is the same.
       If safe_mode is true then you want to play safe: do byte
       by byte comparison for hash duplicate files.
    """
    dups = defaultdict(list)
    # replace dir paths with realpath value (eliminate symbolic links)
    for i in range(len(topdirs)):
        topdirs[i] = os.path.realpath(topdirs[i])
    if verbose:
        if safe_mode:
            print('safe mode is on')
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
            print('\rprocessing file {0}/{1}: calc hash'.format(current,
                                                                count),
                  end='')
            sys.stdout.flush()
        hexmds = [_filehash(fpath, h, block_size) for h in hashalgs]
        hexmd = tuple(hexmds)
        dup_files = dups[hexmd]
        files_equals = False
        if safe_mode:
            if dup_files:
                if verbose:
                    print('\rprocessing file {0}/{1}: byte cmp'.format(current,
                                                                       count),
                          end='')
                    sys.stdout.flush()
                for f in dup_files:
                    if _fbequal(f, fpath):
                        files_equals = True
                        break
                if verbose and not files_equals:
                    print('\nsame hash value {} but not same bytes for file {}'
                          ' with files {}'.format(hexmd, fpath, dup_files))
            else:  # when list is empty in safe mode
                files_equals = True
        else:
            files_equals = True  # when safe mode is off
        if verbose:
            current += 1
        if files_equals:
            dups[hexmd].append(fpath)

    if verbose:
        print('')
    # make result dict with unique file paths list
    result = {}
    for k, v in _dict_iter_items(dups):
        uniq_v = _uniq_list(v)
        if len(uniq_v) > 1:
            result[k] = uniq_v
    return result


def iter_file_dups(topdirs=['./'], hashalgs=['md5'], block_size=4096,
                   safe_mode=False):
    """Find duplicate files in directory list.
       Yield tuple of file path, hash tuple and list of duplicate files
       as soon as duplicate file is found.
       Newly found file is not included in the list at the yield time,
       but is appended later before next yield.
       This means that not all duplicate files are returned with any
       return value. Same hash value and sublist could be returned later
       if file with same content is found.
       If safe_mode is true then you want to play safe: do byte
       by byte comparison for hash duplicate files.
    """
    # internaly, file dups dict is still maintained
    dups = defaultdict(list)
    # replace dir paths with realpath value (eliminate symbolic links)
    for i in range(len(topdirs)):
        topdirs[i] = os.path.realpath(topdirs[i])
    _files_iter = partial(_files_iter_from_disk, topdirs)

    for fpath in _files_iter():
        hexmds = [_filehash(fpath, h, block_size) for h in hashalgs]
        hexmd = tuple(hexmds)
        dup_files = dups[hexmd]
        # there were dup list elements (used for yield)
        if safe_mode and dup_files:
            # compare only with first file in dup_files
            # all files in dup_files list are already content equal
            files_equals =  _fbequal(dup_files[0], fpath)
        else:  # when list is emtpy in safe mode or when safe mode is off
            files_equals = True
        if files_equals:
            # yield only if current dup files list isn't empty
            if dup_files:
                yield (fpath, hexmd, dups[hexmd])
            # finally append newly found file to dup list
            dups[hexmd].append(fpath)


def _extract_files_for_action(topdirs, hashalgs, block_size, keep_prefix,
                              verbose, safe_mode):
    for files in _dict_iter_values(file_dups(topdirs=topdirs,
                                   hashalgs=hashalgs, block_size=block_size,
                                   verbose=verbose, safe_mode=safe_mode)):
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
                 simulate=False, keep_prefix=None, verbose=False,
                 safe_mode=False):
    """Remove duplicate files found in specified directory list.
       If keep_prefix is specified then first file with that path
       prefix found is kept in the original directory.
       Otherwise first file in list is kept in the original directory.
       If simulate is True then only print the action, do not actually
       perform it.
       If safe_mode is true then do byte by byte comparison for
       hash duplicate files.
    """
    for dups, extracted in _extract_files_for_action(topdirs, hashalgs,
                                                     block_size, keep_prefix,
                                                     verbose, safe_mode):
        if simulate or verbose:
            print('found duplicates: \n{}'.format(dups))
        for f in extracted:
            if simulate or verbose:
                print('rm {}'.format(f))
            if not simulate:
                os.remove(f)


def mv_file_dups(topdirs=['./'], hashalgs=['md5'], block_size=4096,
                 dest_dir='dups', simulate=False, keep_prefix=None,
                 verbose=False, safe_mode=False):
    """Move duplicate files found in specified directory list.
       If keep_prefix is specified then first file with that path
       prefix found is kept in the original directory.
       Otherwise first file in list is kept in the original directory.
       If simulate is True then only print the action, do not actually
       perform it.
       If safe_mode is true then do byte by byte comparison for
       hash duplicate files.
    """
    import shutil

    if not os.path.exists(dest_dir):
        if simulate:
            print('mkdir {}'.format(dest_dir))
        else:
            os.mkdir(dest_dir)
    elif not os.path.isdir(dest_dir):
        errmsg = '{} is not a directory'.format(dest_dir)
        if simulate:
            print('would raise:', errmsg)
        else:
            raise OSError(errmsg)
    for dups, extracted in _extract_files_for_action(topdirs, hashalgs,
                                                     block_size, keep_prefix,
                                                     verbose, safe_mode):
        if simulate or verbose:
            print('found duplicates: \n{}'.format(dups))
        for f in extracted:
            if simulate or verbose:
                print('mv {0} to {1}'.format(f, dest_dir))
            if not simulate:
                shutil.move(f, dest_dir)


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
    safe_mode = args['--safe-mode']

    if action == 'print' or action == 'pprint':
        dups = file_dups(topdirs=topdirs,
                         hashalgs=hashalgs,
                         block_size=block_size,
                         verbose=verbose,
                         safe_mode=safe_mode)
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
                     verbose=verbose,
                     safe_mode=safe_mode)
    elif action == 'remove':
        rm_file_dups(topdirs=topdirs, hashalgs=hashalgs,
                     block_size=block_size,
                     simulate=simulate,
                     keep_prefix=keep_prefix,
                     verbose=verbose,
                     safe_mode=safe_mode)
    else:
        print('Invalid action "{}"'.format(action))


if __name__ == '__main__':
    main()
