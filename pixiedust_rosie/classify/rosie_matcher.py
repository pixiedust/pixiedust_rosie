# -------------------------------------------------------------------------------
# Copyright IBM Corp. 2018
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------------

# To install rosie: pip install rosie

from __future__ import unicode_literals, print_function
import six
import json, os, rosie
from .adapt23 import *

# ------------------------------------------------------------------
# Utility functions
#

def most_specific(match):
    while 'subs' in match:
        subs = match['subs']
        if len(subs) > 1: return match
        match = subs[0]
    return match

# Future: Construct these lists by querying the initial Rosie
# environment, just after engine creation.  (Currently, the API for
# this is not in librosie. -- JAJ, April 2018.)
_builtin_refnames = list({b'$', b'.', b'^', b'ci', b'error', b'find', b'findall', b'keepto', b'message', b'~'})

def builtin(refname):
    return bytes23(refname) in _builtin_refnames

_builtin_refnames_no_capture = list({b'$', b'.', b'^', b'ci', b'~'})

def no_capture(refname):
    return bytes23(refname) in _builtin_refnames_no_capture

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

    def json_loads(self, data):
        return json.loads(bytes23(data) if six.PY2 else str23(data))

    def import_pkg(self, pkgname):
        ok, _, messages = self.engine.import_pkg(bytes23(pkgname))
        if not ok:
            raise RuntimeError("RPL package {} failed to load:\n{}".format(pkgname, messages))

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
            return self.json_loads(data)
        raise RuntimeError("pattern 'csv' failed to match: " + raw_data)

    def all(self, raw_data):
        data, leftover, abend, t0, t1 = self.engine.match(self.all_pattern, bytes23(raw_data), 1, b"json")
        if data:
            return self.json_loads(data)
        raise RuntimeError("pattern 'all' failed to match: " + raw_data)

    def compile(self, expression, optional_rpl = None):
        if optional_rpl:
            self.engine.load(bytes23(optional_rpl))
        pat, errs = self.engine.compile(bytes23(expression))
        if not pat:
            raise RuntimeError("expression failed to compile: " + repr(errs))
        return pat

    def match(self, compiled_pattern, raw_data):
        data, leftover, abend, t0, t1 = self.engine.match(compiled_pattern, bytes23(raw_data), 1, b"json")
        if data and (not abend):
            return self.json_loads(data)
        return None

    def extract(self, match_result, component_name):
        component_name = str23(component_name)
        if not match_result: return None
        if (match_result['type'] == component_name):
            return match_result['data']
        elif 'subs' in match_result:
            for sub in match_result['subs']:
                found = self.extract(sub, component_name)
                if found: return found
        return None

    def expression_refs(self, expression):
        refs, errs = self.engine.expression_refs(expression)
        if refs:
            return self.json_loads(refs), errs
        elif errs:
            return refs, self.json_loads(errs)
        else:
            return None, None

    def expression_deps(self, expression):
        deps, errs = self.engine.expression_deps(expression)
        if deps:
            return self.json_loads(deps), errs
        elif errs:
            return deps, self.json_loads(errs)
        else:
            return None, None
