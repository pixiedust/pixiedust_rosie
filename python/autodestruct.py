#  -*- coding: utf-8; -*-
#  -*- Mode: Python; -*-                                              
# 
#  autodestruct.py
# 
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings

# To install rosie: pip install rosie

from __future__ import unicode_literals, print_function

import sys, os, json, rosie_matcher
from adapt23 import str23, bytes23

# ------------------------------------------------------------------
# COMMAND LINE ARGUMENTS
# E.g. python autodestruct <sample_data_file>
#
try:
    datafile = sys.argv[1] 
except IndexError:
    print("Missing required argument: name of data file")
    sys.exit(-1)

# ------------------------------------------------------------------
# Read the sample data line by line,
# apply the destructuring pattern,
# and examine the results.
#

separators = set({'comma', 'semicolon', 'dash', 'slash', 'find.*'})

def fields(m):
    return list(map(lambda s: s['data'],
                    [ sub for sub in most_specific(m)['subs']
                      if (sub['type'] not in separators and (sub['type'] != 'rest' or sub['data'] != '')) ] ))

def describe(m):
    key = most_specific(m)
    return '{} with {} fields'.format(key['type'], len(fields(m)))

matcher = rosie_matcher.Matcher()
matcher.loadfile('destructure.rpl')
pat = matcher.compile('destructure.tryall')

print('{:40} {:30} {}'.format('Field contents', 'Recognized as', 'Suggested destructuring'))
print()
with open(datafile) as f:
    for datum in f.readlines():
        m = matcher.match(pat, datum.strip())
        if not m:
            print(datum.rstrip(), "has no structure that we can recognize")
        print('{:40} {:30} {}'.format(datum.rstrip(), describe(m), fields(m)))


## Some testing of Matcher below:

matcher.load('foobar')
