#  -*- Mode: Python; -*-                                              
#  -*- coding: utf-8; -*-
# 
#  matcher.py
# 
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings

# To install rosie: pip install rosie

from __future__ import unicode_literals, print_function
import json, os, rosie
from adapt23 import str23, bytes23

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
        # Check to see if user prefers to use their own installation
        # of rosie, or one already installed on their system.
        rosie_home = os.getenv('ROSIE_HOME')
        if rosie_home: rosie.load(os.path.join(rosie_home, 'src/librosie/local'))
        self.engine = rosie.engine()
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
        if data and (not abend) and (leftover == 0):
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

