# -*- coding: utf-8 -*-
__author__ = 'whiteworld'

import hashlib
BLOCKSIZE = 65536
hasher = hashlib.md5()


def hashfile(filename):
    with open(filename, 'rb') as afile:
        buf = afile.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(BLOCKSIZE)
    return hasher.hexdigest()
