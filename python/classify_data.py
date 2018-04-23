#  -*- coding: utf-8; -*-
#  -*- Mode: Python; -*-
#
#  classify_data.py
#
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings

# To install rosie: pip install rosie

from __future__ import unicode_literals, print_function

import sys, os, json, rosie_matcher
from adapt23 import *

# ------------------------------------------------------------------
# Error messages
#

error_no_pattern = 'Please enter a pattern to apply to the column'
error_empty_expression = 'Please enter a pattern expression'

def error_syntax(rosie_errs):
    # TODO: pretty printing of errs
    return "Syntax error in pattern:\n" + repr(rosie_errs)

def error_parsing(rosie_errs):
    # TODO: pretty printing of errs
    return "Error parsing expression:\n" + repr(rosie_errs)

def error_missing_dependency(pkgname, rosie_errs):
    # TODO: pretty printing of errs
    return "Cannot find RPL pattern package {}:\n{}".format(pkgname, repr(rosie_errs))

def error_compiling(rosie_errs):
    # TODO: pretty printing of errs
    return "Pattern failed to compile: " + repr(rosie_errs)

def error_loading_rpl(rosie_errs):
    # TODO: pretty printing of errs
    return "Patterns failed to load: " + repr(rosie_errs)


# ------------------------------------------------------------------
# Utility functions
#

def most_specific(match):
    while 'subs' in match:
        subs = match['subs']
        if len(subs) > 1: return match
        match = subs[0]
    return match

def ref_to_name(ref):
    assert('ref' in ref)
    ref = ref['ref']
    if 'packagename' in ref:
        return ref['packagename'] + '.' + ref['localname'], True
    else:
        return ref['localname'], False

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
        self.transform = None

    # ------------------------------------------------------------------
    # Process
    #
    def load_and_process(self):
        self.matcher = rosie_matcher.Matcher()
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
        self.colnames = list(map23(lambda sub: sub['data'].rstrip(), csv['subs']))
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
    # Create a component pattern for each reference in the transformer pattern
    #
    def set_transform_components(self, transformer):
        if (not transformer._pattern) or (not transformer._pattern._definition):
            transformer.errors = error_no_pattern
            return False
        refs, errs = self.matcher.expression_refs(transformer._pattern._definition)
        if (not refs) and errs:
            transformer.errors = error_syntax(errs)
            return False
        name_tuples = map23(ref_to_name, refs)
        needing_definitions = set(map23(lambda t: t[0], filter(lambda t: not t[1], name_tuples)))
        not_needing_definitions = set(map23(lambda t: t[0], filter(lambda t: t[1], name_tuples)))
        new_components = map23(lambda name: Pattern(name, None), needing_definitions)
        new_components.extend(map23(lambda name: Pattern(name, False), not_needing_definitions))
        if transformer.components:
            for c in new_components:
                existing = False
                for pat in transformer.components:
                    if pat._name == c._name:
                        existing = pat
                        break
                if existing:
                    c._definition = existing._definition
        transformer.components = new_components
        return True
    
    # ------------------------------------------------------------------
    # Compute and set the dependencies in all of a transformer patterns
    #
    def find_imports(self, expression):
        if not expression:
            return RuntimeError(error_empty_expression)
        imports, errs = self.matcher.expression_deps(expression)
        if (not imports) and errs:
            return RuntimeError(error_parsing(errs))
        return imports or list()

    def set_transform_imports(self, transformer):
        imports = self.find_imports(transformer._pattern._definition)
        if isinstance(imports, RuntimeError):
            transformer.errors = str(imports)
            return False
        transformer.imports = imports
        final_status = True
        for pat in transformer.components:
            if pat._definition is not False:
                imports = self.find_imports(pat._definition)
                if isinstance(imports, RuntimeError):
                    if transformer.errors:
                        transformer.errors = transformer.errors  + '\n' + str(imports)
                    else:
                        transformer.errors = str(imports)
                    final_status = False
                else:
                    if imports: transformer.imports.extend(imports) 
        return final_status

    # ------------------------------------------------------------------
    # Create column(s) via a Rosie pattern applied to an existing
    # column.  Return the new columns, without adding them into the
    # Schema.  To change the Schema to include them, use
    # commit_new_columns.
    #
    def new_columns(self, transformer):
        transformer.errors = None
        if not self.set_transform_components(transformer):
            return False
        if not self.set_transform_imports(transformer):
            return False
        if transformer.imports:
            for pkg in transformer.imports:
                ok, _, errs = self.matcher.engine.import_pkg(bytes23(pkg))
                if not ok:
                    transform.errors = error_missing_dependency(pkg, errs)
        optional_rpl = transformer.generate_rpl()
        if optional_rpl:
            ok, _, errs = self.matcher.engine.load(bytes23(optional_rpl))
            if not ok:
                transformer.errors = error_loading_rpl(errs)
                return False
        pat, errs = self.matcher.engine.compile(bytes23(transformer._pattern._definition))
        if not pat:
            transformer.errors = error_compiling(errs)
            return False
        colnum = transformer._colnum
        component_names = map23(lambda c: str23(c._name), transformer.components)
        newcols = list(map23(lambda cn: list(), component_names))
        for rownum, row in enumerate(self.sample_data):
            m = self.matcher.match(pat, row[colnum])
            for compnum, cn in enumerate(component_names):
                datum = self.matcher.extract(m, cn)
                newcols[compnum].append(datum)
        return newcols

    def commit_new_columns(self, transformer):
        newcols = self.new_columns(transformer)
        if not newcols: return False
        self.cols += len(transformer.components)
        for i, component in enumerate(transformer.components):
            newcolnum = transformer._colnum + i + 1
            cn = str23(component._name)
            # Sample data and its types are stored by row
            for rownum in range(len(self.sample_data)):
                self.sample_data[rownum].insert(newcolnum, newcols[i][rownum])
                self.sample_data_types[rownum].insert(newcolnum, cn)
            # The other fields are column-oriented
            self.column_visibility.insert(newcolnum, True)
            self.colnames.insert(newcolnum, cn)
            self.rosie_types.insert(newcolnum, cn)
            self.synthetic_column.insert(newcolnum,
                                              {'col': transformer._colnum,
                                               'exp': component._definition,
                                               'name': cn,
                                               'rpl': transformer.generate_rpl()
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
                        best_match_type = Schema_record_type(list(map23(lambda s: s['subs'][0]['type'], best['subs'])))
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
        self.rpl = list(map23(lambda c: None, self.rosie_types))
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

    def create_schema_table(self):
        return zip23(self.column_visibility, self.colnames, self.rosie_types, self.native_types)

    def rename_column(self,colnum, new_name):
        self.colnames[colnum] = new_name

    def create_transform(self, colnum):
        self.transform = Transform(colnum)

# ------------------------------------------------------------------
# Transform: Everything needed to transform a column of data into one
# or more new columns, using a Rosie pattern.
#

class Transform:

    def __init__(self, colnum, pat_definition_rpl=None):
        assert(isinstance(colnum, int))
        self._colnum = colnum
        self._pattern = Pattern(None, pat_definition_rpl)
        self.components = None  # list of patterns
        self.imports = None
        self.errors = None

    def generate_rpl(self):
        rpl = b''
        for pat in self.components:
            if pat._definition:
                rpl = rpl + pat._name + b'=' + pat._definition + b';\n'
        return rpl

class Pattern:

    def __init__(self, name, definition=None):
        self._name = bytes23(name) if name else None
        self._definition = bytes23(definition) if definition else definition

# ------------------------------------------------------------------
# Map the rosie types to pandas scalar type
#
# Pandas supports scalars and arrays, where arrays may be of other arrays or
# of scalars.  The scalar types appear to be the ones supported by numpy,
# which are listed in numpy.ScalarType.

#available_types = {int, float, complex, bool, str, unicode, buffer}

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
    converted_sample_data = zip23(*converted_sample_data_by_col)
    colnum = 0
    for label, datum, rtype, ntype, converted in zip23(s.colnames,
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
