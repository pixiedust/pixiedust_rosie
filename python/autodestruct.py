#  -*- coding: utf-8; -*-
#  -*- Mode: Python; -*-                                              
# 
#  autodestruct.py
# 
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings

# Requires rosie to be installed (such as in the system location, like
# /usr/local) or at least downloaded and built.  To run rosie out of
# the download directory, set the environment variable ROSIE_HOME to
# the rosie download directory, e.g.
#
# export ROSIE_HOME='/Users/jjennings/Work/Dev/public/rosie-pattern-language'
#

from __future__ import unicode_literals, print_function

import sys, os, json, rosie


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
# Adapt to work with python 2 or 3
#
try:
    HAS_UNICODE_TYPE = type(unicode) and True
    str23 = lambda s: str(s)
    bytes23 = lambda s: bytes(s)
except NameError:
    HAS_UNICODE_TYPE = False
    str23 = lambda s: str(s, encoding='UTF-8')
    bytes23 = lambda s: bytes(s, encoding='UTF-8')

# ------------------------------------------------------------------
# Utility functions
#

def most_specific(match):
    while 'subs' in match:
        subs = match['subs']
        if len(subs) > 1: return match
        match = subs[0]
    return match
        
# ------------------------------------------------------------------
# Rosie matching functions
#

class Matcher():

    def __init__(self):
        rosie_home = os.getenv('ROSIE_HOME')
        self.engine = rosie.engine(os.path.join(rosie_home, 'src/librosie/local') if rosie_home else None)
        self.engine.import_pkg(b'all')
        self.engine.import_pkg(b'csv')
        self.csv_pattern, errs = self.engine.compile(b'csv.comma')
        self.all_pattern, errs = self.engine.compile(b'all.things')

    def loadfile(self, filename):
        ok, _, messages = self.engine.loadfile(bytes23(filename))
        if not ok:
            raise RuntimeError("file {} failed to load:\n{}".format(filename, messages))
        
    def load(self, rpl_block):
        ok, _, messages = self.engine.load(bytes23(rpl_block))
        if not ok:
            raise RuntimeError("rpl code block ({}...) failed to load:\n{}".format(rpl_block[:20], messages))
        
    def csv(self, raw_data):
        data, leftover, abend, t0, t1 = self.engine.match(self.csv_pattern, bytes23(raw_data), 1, b"json")
        if data:
            return json.loads(data)
        raise RuntimeError("pattern 'csv' failed to match: " + raw_data)

    def all(self, raw_data):
        data, leftover, abend, t0, t1 = self.engine.match(self.all_pattern, bytes23(raw_data), 1, b"json")
        if data:
            return json.loads(data)
        raise RuntimeError("pattern 'all' failed to match: " + raw_data)

    def compile(self, pattern_name, optional_rpl = None):
        if optional_rpl: self.engine.load(bytes23(optional_rpl))
        pat, errs = self.engine.compile(bytes23(pattern_name))
        if not pat:
            raise RuntimeError("pattern '" + pattern_name + "' failed to compile: " + errs)
        return pat

    def match(self, compiled_pattern, raw_data):
        data, leftover, abend, t0, t1 = self.engine.match(compiled_pattern, bytes23(raw_data), 1, b"json")
        if data:
            return json.loads(data)
        return None

    def extract(self, match_result, component_name):
        if not match_result: return None
        if (match_result['type'] == component_name):
            return match_result['data']
        elif 'subs' in match_result:
            for sub in match_result['subs']:
                found = self.extract(sub, component_name)
                if found: return found
        return None

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

matcher = Matcher()
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
