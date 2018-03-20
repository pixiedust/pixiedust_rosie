#  -*- coding: utf-8; -*-
#  -*- Mode: Python; -*-                                              
# 
#  classify_data.py
# 
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings


from __future__ import unicode_literals, print_function

import sys, json, rosie

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
# Schema column types that are not strings
#

class Schema_type_class:
    __names = set()
    def __init__(self, name):
        if name in self.__names:
            raise ValueError('Schema type already defined')
        self.__names.add(name)
        self.name = name
    def __str__(self):
        return self.name
    def __repr__(self):
        return self.name

Schema_any_type = Schema_type_class('<any>')
Schema_empty_type = Schema_type_class('<empty>')

# ------------------------------------------------------------------
# Schema -- this is the main object
#

class Schema:
    ANY = Schema_any_type
    EMPTY = Schema_empty_type
    
    def __init__(self, colnames):
        self.colnames = colnames
        self.cols = len(colnames)
        self.sample_data = None           # all requested rows
        self.sample_data_types = None     # rosie types for the original data
        self.rosie_types = None           # "final" set of rosie types
        self.native_types = None          # rosie types mapped onto native types
        self.inconsistent_rows = list()   # list of (rownum, rowdata)
        self.colmask = None
        self.type_map = default_type_map.copy()
        self.engine = None

    # ------------------------------------------------------------------
    # Process
    #
    def process_sample_data(self):
        self.do_consistency_check()
        self.resolve_type_ambiguities()
        self.assign_native_types()
        self.colmask = [True for _ in self.colnames]

    # ------------------------------------------------------------------
    # Hide column
    #
    def hide_column(self, colnum):
        self.colmask[colnum] = False

    # ------------------------------------------------------------------
    # Change column's native type
    #



    # ------------------------------------------------------------------
    # Create column(s) via a Rosie pattern applied to an existing column
    #
    


    # ------------------------------------------------------------------
    # Check for consistent number of columns, taking the number of column
    # names as canonical.  Delete any rows that do not conform.
    #
    def do_consistency_check(self):
        for i, row in enumerate(self.sample_data):
            if len(row) != self.cols:
                self.inconsistent_rows.append( (i, row) )
                del(self.sample_data_types[i])
                del(self.sample_data[i])

    # ------------------------------------------------------------------
    # Find ambiguous Rosie types within the sample data, and change
    # rosie_types[col] for each such col to Schema_any_type.
    #
    # We will take the types of the first row of data as canonical.  In
    # the future, we should probably do something more sophisticated.
    #
    def resolve_type_ambiguities(self):
        self.rosie_types = self.sample_data_types[0][:]
        for col in range(0, len(self.sample_data_types[0])):
            for row in range(1, len(self.sample_data_types)):
                if self.rosie_types[col] is not Schema_any_type:
                    if self.sample_data_types[row][col] != self.rosie_types[col]:
                        self.rosie_types[col] = Schema_any_type

    # ------------------------------------------------------------------
    # Build the list of native types by mapping from self.rosie_types
    #
    def assign_native_types(self):
        ntypes = list()
        for col in range(0, self.cols):
            ntypes.append(map_type(self.rosie_types[col], self.type_map))
        self.native_types = ntypes


# ------------------------------------------------------------------
# Load sample data from file and create initial schema object
#

def load_sample_data(filename, samplesize):
    match = matcher()
    f = open(filename)
    csv = match.csv(f.readline())
    colnames = list(map(lambda sub: sub['data'].rstrip(), csv['subs']))
    s = Schema(colnames)
    s.sample_data_types = list()
    s.sample_data = list()
    for i in range(samplesize):
        rowstring = f.readline().rstrip()
        csv = match.csv(rowstring)
        row = list()
        for item in csv['subs']:
            if 'subs' in item:
                datum = item['subs'][0]['data']
            else:
                datum = item['data']
            row.append(datum or False)
        s.sample_data.append(row)
        s.sample_data_types.append(list())
        for col in row:
            if not col:
                # No data in this field
                s.sample_data_types[i].append(s.EMPTY)
            else:
                m = match.all(col)
                best = most_specific(m)
                if best['type'] == 'all.things':
                    best_match_type = list(map(lambda s: s['subs'][0]['type'], best['subs']))
                else:
                    best_match_type = best['type']
                s.sample_data_types[i].append(best_match_type)
    return s


# ------------------------------------------------------------------
# Rosie matching functions
#

class matcher():

    def __init__(self):
        self.engine = rosie.engine()
        self.engine.import_pkg(b'all')
        self.engine.import_pkg(b'csv')
        self.csv_pattern, errs = self.engine.compile(b'csv.comma')
        self.all_pattern, errs = self.engine.compile(b'all.things')

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


# ------------------------------------------------------------------
# Map the rosie types to numpy types
#

default_type_map = {'num.int': int,
                    'num.float': float,
                    'num.mantissa': float,
                    'all.identifier': str,
                    'word.any': str
}

def map_type(rtype, type_map):
    if type(rtype) is list:
        return str
    elif rtype is Schema_any_type:
        return str
    elif rtype is Schema_empty_type:
        return str
    elif rtype in type_map:
        return type_map[rtype]
    else:
        raise ValueError('No defined transformation for Rosie type ' + repr(rtype))


# ----------------------------------------------------------------------------------------
# Print functions for debugging
#

def print_sample_data_verbosely(s, rownum):
    print('  ',
          '#'.ljust(5),
          'Label'.ljust(20),
          'Rosie type'.ljust(22),
          'Native type'.ljust(16),
          '  ',
          'Sample data'.ljust(20),
          'Converted')
    print()
    colnum = 0
    for label, datum, rtype, ntype in zip(s.colnames, s.sample_data[rownum], s.rosie_types, s.native_types):
        num = repr(colnum).ljust(5)
        label = label[:20].ljust(20)
        d = (datum and repr(datum)[:20] or "").ljust(20)
        rt = repr(rtype)[:22].ljust(22)
        nt = repr(ntype)[:16].ljust(16)
        converted = ntype(datum or '')
        deleted_ = s.colmask[colnum] and '  ' or '[ '
        _deleted = s.colmask[colnum] and '  ' or ' ]'
        print(deleted_, num, label, rt, '=>', nt, d, str(converted)[:40], _deleted)
        colnum = colnum + 1


def print_sample_data_column(s, colnum):
    rtype = s.rosie_types[colnum]
    print("Column", colnum, "has label", repr(s.colnames[colnum]), "and has",
          (rtype is s.ANY) and "ambiguous type" or "type " + rtype)
    print("Here is sample data:")
    for rownum, row in enumerate(s.sample_data):
        rownum = repr(rownum).ljust(5)
        data = repr(row[colnum] or "False")
        print('  row', rownum, data[:30].ljust(30))

def print_ambiguously_typed_columns(s):
    for colnum, rtype in enumerate(s.rosie_types):
        if rtype is s.ANY:
            print_sample_data_column(s, colnum)


# ----------------------------------------------------------------------------------------
# 
#
