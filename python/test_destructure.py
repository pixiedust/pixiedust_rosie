#  -*- coding: utf-8; -*-
#  -*- Mode: Python; -*-                                              
# 
#  test_destructure.py
# 
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings

# To install rosie: pip install rosie

from __future__ import unicode_literals, print_function

import sys, destructure, rosie_matcher
from adapt23 import *

# ------------------------------------------------------------------
# COMMAND LINE ARGUMENTS
#    python test_autodestruct <sample_data_file>
# where <sample_data_file> has one structured field on each line,
# and each line can be a different format.
try:
    datafile = sys.argv[1] 
except IndexError:
    print("Missing required argument: name of data file")
    sys.exit(-1)

def describe(key, fields):
    return '{} with {} fields'.format(key['type'], len(fields))

matcher = rosie_matcher.Matcher()
destructure_pattern = destructure.compile(matcher)

print('{:40} {:30} {}'.format('Field contents', 'Recognized as', 'Suggested destructuring'))
print()
with open(datafile) as f:
    for datum in f.readlines():
        key, fields = destructure.match(destructure_pattern, matcher, datum)
        if not key:
            print(datum.rstrip(), "has no structure that we can recognize")
        else:
            print('{:40} {:30} {}'.format(datum.rstrip(), describe(key, fields), map(lambda f: f['data'], fields)))



