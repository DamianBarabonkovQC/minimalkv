#!/usr/bin/env python
# coding=utf8

import os

from . import KeyValueStorage


class FilesystemStore(KeyValueStorage):
    """Store data in files on the filesystem.

    The *FilesystemStore* stores every value as its own file on the filesystem,
    all under a common directory.
    """
    def __init__(self, root):
        """Initialize new FilesystemStore

        :param root: the base directory for the store
        """
        self.root = root
        self.bufsize = 2 ** 32 - 1

    def _build_filename(self, key):
        return os.path.join(self.root, key)

    def _get(self, key):
        return self._open(key).read()

    def _open(self, key):
        try:
            f = file(self._build_filename(key), 'rb')
            return f
        except IOError, e:
            if 2 == e.errno:
                raise KeyError(key)
            else:
                raise

    def _put_data(self, key, data):
        with file(self._build_filename(key), 'wb') as f:
            f.write(data)

    def _put_readable(self, key, source):
        bufsize = self.bufsize
        with file(self._build_filename(key), 'wb') as f:
            while True:
                buf = source.read(bufsize)
                f.write(buf)
                if len(buf) < bufsize:
                    break