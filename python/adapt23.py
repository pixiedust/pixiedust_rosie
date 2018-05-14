#  -*- Mode: Python; -*-                                              
#  -*- coding: utf-8; -*-
# 
#  adapt23.py
# 
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings


# ------------------------------------------------------------------
# Adapt to work with python 2 or 3
#

try:
    HAS_UNICODE_TYPE = type(unicode) and True
    str23 = lambda s: str(s)
    bytes23 = lambda s: bytes(s)
    zip23 = zip
    map23 = map
    filter23 = filter
except NameError:
    HAS_UNICODE_TYPE = False
    def bytes23(s):
        if isinstance(s, str):
            return bytes(s, encoding='UTF-8')
        elif isinstance(s, bytes):
            return s
        else:
            raise ValueError('obj not str or bytes: ' + repr(type(s)))
    def str23(s):
        if isinstance(s, str):
            return s
        elif isinstance(s, bytes):
            return str(s, encoding='UTF-8')
        else:
            raise ValueError('obj not str or bytes: ' + repr(type(s)))
    def zip23(*args):
        return list(zip(*args))
    def map23(fn, *args):
        return list(map(fn, *args))
    def filter23(fn, *args):
        return list(filter(fn, *args))
    
