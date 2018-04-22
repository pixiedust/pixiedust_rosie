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
except NameError:
    HAS_UNICODE_TYPE = False
    str23 = lambda s: str(s, encoding='UTF-8')
    bytes23 = lambda s: bytes(s, encoding='UTF-8')
    def zip23(*args):
        return list(zip(*args))
    def map23(fn, *args):
        return list(map(fn, *args))
    