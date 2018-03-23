#  -*- coding: utf-8; -*-
#  -*- Mode: Python; -*-                                              
# 
#  classify_data.py
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

class Schema_record_type:
    def __init__(self, parameters):
        if type(parameters) != list:
            raise TypeError("Schema_record_type requires a single parameter list")
        self.parameters = parameters
    def __str__(self):
        return '<record>'
    def __repr__(self):
        return repr(self.parameters)

# ------------------------------------------------------------------
# Schema -- this is the main object
#

class Schema:
    
    def __init__(self, filename, samplesize):
        self.filename = filename
        self.samplesize = samplesize
        self.matcher = None               # Rosie matcher
        self.colnames = None              # First line of csv input
        self.cols = None                  # Number of columns
        self.sample_data = None           # All requested rows
        self.sample_data_types = None     # Rosie types for all rows
        self.rosie_types = None           # Final set of rosie types
        self.rpl = None                   # Optional rpl to load prior to using rosie_types
        self.native_types = None          # Pandas/Numpy types mapped from rosie_types
        self.inconsistent_rows = None     # list of (rownum, rowdata) tuples
        self.column_visibility = None     # list of booleans, True=visible
        self.type_map = default_type_map.copy()

    # ------------------------------------------------------------------
    # Process
    #
    def load_and_process(self):
        self.matcher = Matcher()
        self.load_sample_data()
        assert(self.sample_data)
        self.set_number_of_cols()
        assert(self.cols)
        self.rectangularize()
        self.generate_rosie_types()
        assert(self.sample_data_types)
        self.resolve_type_ambiguities()
        assert(len(self.rosie_types)==self.cols)
        self.assign_native_types()
        self.column_visibility = [True for _ in self.colnames]
        self.synthetic_column = [False for _ in self.colnames]

    # ------------------------------------------------------------------
    # Load sample data from file
    #
    def load_sample_data(self):
        f = open(self.filename)
        csv = self.matcher.csv(f.readline())
        self.colnames = list(map(lambda sub: sub['data'].rstrip(), csv['subs']))
        self.sample_data = list()
        for i in range(self.samplesize):
            rowstring = f.readline().rstrip()
            csv = self.matcher.csv(rowstring)
            row = list()
            for item in csv['subs']:
                if 'subs' in item:
                    datum = item['subs'][0]['data']
                else:
                    datum = item['data']
                row.append(datum or None)
            self.sample_data.append(row)

    # ------------------------------------------------------------------
    # We can be smarter about this in the future
    #
    def set_number_of_cols(self):
        self.cols = len(self.colnames)

    # ------------------------------------------------------------------
    # Try to convert the raw data to the assigned native type
    #
    def convert(self, colnum, error_value = None):
        ntype = self.native_types[colnum]
        converted = list()
        failures = list()
        for rownum, row in enumerate(self.sample_data):
            try:
                datum = ntype(row[colnum])
            except:
                datum = error_value
                failures.append(rownum)
            converted.append(datum)
        return converted, failures

    # ------------------------------------------------------------------
    # Hide column
    #
    def hide_column(self, colnum):
        self.column_visibility[colnum] = False

    # ------------------------------------------------------------------
    # Change column's native type assignment
    #
    def set_native_type(self, colnum, conversion_fn):
        self.native_types[colnum] = conversion_fn

    # ------------------------------------------------------------------
    # Create column(s) via a Rosie pattern applied to an existing column
    #
    def new_columns(self, colnum, expression, component_names, optional_rpl=None):
        pat = self.matcher.compile(expression, optional_rpl)
        newcols = list(map(lambda cn: list(), component_names))
        for rownum, row in enumerate(self.sample_data):
            m = self.matcher.match(pat, row[colnum])
            for compnum, cn in enumerate(component_names):
                datum = self.matcher.extract(m, cn)
                newcols[compnum].append(datum)
        return newcols

    def commit_new_columns(self, colnum, expression, component_names, optional_rpl=None):
        newcols = self.new_columns(colnum, expression, component_names, optional_rpl)
        self.cols += len(component_names)
        for i, cn in enumerate(component_names):
            newcolnum = colnum + i + 1
            # Sample data and its types are stored by row
            for rownum in range(len(self.sample_data)):
                self.sample_data[rownum].insert(newcolnum, newcols[i][rownum])
                self.sample_data_types[rownum].insert(newcolnum, cn)
            # The other fields are column-oriented
            self.column_visibility.insert(newcolnum, True)
            self.colnames.insert(newcolnum, cn)
            self.rosie_types.insert(newcolnum, cn)
            self.synthetic_column.insert(newcolnum,
                                              {'col': colnum,
                                               'exp': expression,
                                               'name': cn,
                                               'rpl': optional_rpl
                                              })
            if not (cn in self.type_map):
                # Use a default native type, which the user can change later
                self.type_map[cn] = str
            self.assign_native_type(newcolnum)
        
    # ------------------------------------------------------------------
    # Delete any rows (actually remove them) that do not have the right
    # number of columns.  In the future maybe we could use heuristics or
    # user guidance to fix these rows.  On exit, self.sample_data is
    # rectangular.
    #
    def rectangularize(self):
        self.inconsistent_rows = list()
        for i, row in enumerate(self.sample_data):
            if len(row) != self.cols:
                self.inconsistent_rows.append( (i, row) )
                del(self.sample_data[i])

    # ------------------------------------------------------------------
    # Create (or overwrite) self.sample_data_types
    #
    def generate_rosie_types(self):
        self.sample_data_types = list()
        for i, row in enumerate(self.sample_data):
            self.sample_data_types.append(list())
            for col in row:
                if not col:
                    # No data in this field
                    self.sample_data_types[i].append(Schema_empty_type)
                else:
                    m = self.matcher.all(col)
                    best = most_specific(m)
                    if best['type'] == 'all.things':
                        best_match_type = Schema_record_type(list(map(lambda s: s['subs'][0]['type'], best['subs'])))
                    else:
                        best_match_type = best['type']
                    self.sample_data_types[i].append(best_match_type)

    # ------------------------------------------------------------------
    # Find ambiguous Rosie types within the sample data, and change
    # rosie_types[col] for each such col to Schema_any_type.
    #
    # Assumes every row of sample_data has self.cols columns.
    #
    # We will take the types of the first row of data as canonical.  In
    # the future, we should probably do something more sophisticated.
    #
    def resolve_type_ambiguities(self):
        self.rosie_types = self.sample_data_types[0][:]
        self.rpl = list(map(lambda c: None, self.rosie_types))
        for col in range(0, self.cols):
            for row in range(1, len(self.sample_data_types)):
                rtype = self.rosie_types[col]
                if rtype is Schema_any_type:
                    # matches anything
                    continue
                elif isinstance(rtype, Schema_record_type):
                    # matches only another record type with the same slots
                    item_type = self.sample_data_types[row][col]
                    if isinstance(item_type, Schema_record_type):
                        if item_type.parameters == rtype.parameters:
                            continue
                elif self.sample_data_types[row][col] == rtype:
                    # these types are rosie pattern names, which must match exactly
                    continue
                self.rosie_types[col] = Schema_any_type

    # ------------------------------------------------------------------
    # Build the list of native types by mapping from self.rosie_types
    #
    def assign_native_type(self, colnum):
        self.native_types.insert(colnum,
                                 map_type(self.rosie_types[colnum],
                                          self.type_map))

    def assign_native_types(self):                                     
        self.native_types = list()
        for col in range(0, self.cols):
            self.assign_native_type(col)

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
# Map the rosie types to pandas scalar type
#
# Pandas supports scalars and arrays, where arrays may be of other arrays or
# of scalars.  The scalar types appear to be the ones supported by numpy,
# which are listed in numpy.ScalarType.

available_types = {int, float, complex, long, bool, str, unicode, buffer}

# We are TEMPORARILY not including the numpy types in the list of available
# types.  They are:
# <type 'numpy.unicode_'>, <type 'numpy.datetime64'>, <type 'numpy.uint64'>,
# <type 'numpy.int64'>, <type 'numpy.void'>, <type 'numpy.timedelta64'>,
# <type 'numpy.float16'>, <type 'numpy.uint8'>, <type 'numpy.int8'>,
# <type 'numpy.object_'>, <type 'numpy.complex64'>, <type 'numpy.float32'>,
# <type 'numpy.uint16'>, <type 'numpy.int16'>, <type 'numpy.bool_'>,
# <type 'numpy.complex128'>, <type 'numpy.float64'>, <type 'numpy.uint32'>,
# <type 'numpy.int32'>, <type 'numpy.string_'>, <type 'numpy.complex256'>,
# <type 'numpy.float128'>, <type 'numpy.uint64'>, <type 'numpy.int64'>

default_type_map = {Schema_any_type: str,
                    Schema_empty_type: lambda x: None,
                    Schema_record_type: str,
                    'num.int': int,
                    'num.float': float,
                    'num.mantissa': float,
                    'all.identifier': str,
                    'word.any': str
}

def map_type(rtype, type_map):
    if isinstance(rtype, Schema_record_type):
        conversion_fn = type_map[Schema_record_type]
    elif rtype in type_map:
        conversion_fn = type_map[rtype]
    else:
        raise ValueError('No defined transformation for Rosie type ' + repr(rtype))
    return conversion_fn

# ----------------------------------------------------------------------------------------
# Print functions for debugging
#

def print_sample_data_verbosely(s, rownum):
    print('  ',
          '#'.ljust(5),
          'Label'.ljust(20),
          'Rosie type'.ljust(18),
          'Native type'.ljust(16),
          '  ',
          'Sample data'.ljust(20),
          'Converted')
    print()
    # The convert() method returns converted data list and failure list.
    converted_sample_data_by_col = [s.convert(colnum, '<fail>')[0] for colnum in range(0, s.cols)]
    # The prefix '*' to an argument to zip transposes the arg.
    converted_sample_data = zip(*converted_sample_data_by_col)
    colnum = 0
    for label, datum, rtype, ntype, converted in zip(s.colnames,
                                                     s.sample_data[rownum],
                                                     s.rosie_types,
                                                     s.native_types,
                                                     converted_sample_data[rownum]):
        num = repr(colnum).ljust(5)
        label = label[:20].ljust(20)
        d = (datum and repr(datum)[:20] or "").ljust(20)
        rt = repr(rtype)[:18].ljust(18)
        nt = repr(ntype)[:16].ljust(16)
        deleted_ = s.column_visibility[colnum] and ' ' or '['
        _deleted = s.column_visibility[colnum] and ' ' or ']'
        synthetic = s.synthetic_column[colnum] and '+' or ' '
        print(deleted_, synthetic, num, label, rt, '=>', nt, d, str(converted)[:40], _deleted)
        colnum = colnum + 1


def print_sample_data_column(s, colnum):
    rtype = s.rosie_types[colnum]
    print("Column", colnum, "has label", repr(s.colnames[colnum]), "and has",
          (rtype is Schema_any_type) and "ambiguous type" or "type " + rtype)
    print("Here is sample data:")
    for rownum, row in enumerate(s.sample_data):
        rownum = repr(rownum).ljust(5)
        data = repr(row[colnum] or "False")
        print('  row', rownum, data[:30].ljust(30))

def print_ambiguously_typed_columns(s):
    for colnum, rtype in enumerate(s.rosie_types):
        if rtype is Schema_any_type:
            print_sample_data_column(s, colnum)


# ----------------------------------------------------------------------------------------
# 
#
