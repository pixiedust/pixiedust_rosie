# coding: utf-8
#  -*- Mode: Python; -*-                                              

from __future__ import unicode_literals, print_function

import sys, json, rosie
import classify.classify_data as classify_data
import classify.rosie_matcher as rosie_matcher
import classify.destructure as destructure
from classify.adapt23 import *

# ------------------------------------------------------------------
# COMMAND LINE ARGUMENTS
# E.g. python test_classify_data ../data/HCUP-err1.csv 20
#
try:
    datafile = sys.argv[1] 
except IndexError:
    print("Missing required argument: name of data file")
    sys.exit(-1)
try:
    samplesize = sys.argv[2]
except IndexError:
    samplesize = 1

samplesize = int(samplesize)    

def test():
    s = classify_data.Schema(datafile, samplesize)
    ok, err = s.load_and_process()
    if not ok:
        raise RuntimeError('failed to load sample data: ' + err)

    for removed_row in s.inconsistent_rows:
        i, row = removed_row
        if len(row) > s.cols:
            print("row", i, "has too many columns", s.sample_data[i])
        else:
            print("row", i, "has too few columns", s.sample_data[i])

    print()
    print("In a sample of", samplesize, "rows, we excluded", len(s.inconsistent_rows),
          "rows which did not have the expected number of columns.")

    print("\nData has", s.cols, "columns, and sample set has", len(s.sample_data), "rows")
    print()

    print()
    print("For demonstration purposes, we will delete columns 4-6 and 22-end...")
    for i in range(4, 8):
        s.hide_column(i)
    for i in range(22, s.cols):
        s.hide_column(i)

    print()
    classify_data.print_sample_data_verbosely(s, 0)

    print()
    classify_data.print_ambiguously_typed_columns(s)


    if False:
        print()
        print("Sample data with visible columns only")
        for row in s.sample_data:
            visible = [datum for i, datum in enumerate(row) if s.column_visibility[i]]
            print(visible)

        for c in range(0, s.cols):
            data, errs = s.convert(c)
            print(c, data)
            print(c, "rows that failed:", errs)

    print()
    print("Now we change the native type of column 0 to float:")
    s.set_native_type(0, float)
    print(0, s.convert(0))

    print()
    print("Now we change the native type of column 11 to complex: (it should fail)")
    s.set_native_type(11, complex)
    print(11, s.convert(11, '*FAIL*'))

    print()
    print("Make a new column based on column 26 to extract the numeric part:")
    s.transformer = classify_data.Transform(26)
    new = s.new_columns()
    assert( new is False )
    assert( 'pattern' in s.transformer.errors ) # Please enter a pattern

    s.transformer = classify_data.Transform(26, '{[^0-9]* n}')
    new = s.new_columns()
    assert( new is False )
    assert( 'pattern' in s.transformer.errors ) # Please enter a pattern

    assert(len(s.transformer.components) == 1)
    pat = s.transformer.components[0]
    assert(pat._name == b'n')
    assert(pat._definition is None)
    pat._definition = b'[0-9]*'

    new = s.new_columns()
    assert( new )
    assert( s.transformer.errors == None )
    # print('*** pattern:', tr1._pattern._definition)
    # print('*** components:', map23(lambda c: (c._name, c._definition), tr1.components))
    # print('*** imports:', tr1.imports)

    print(new)

# ---------------------------------------------------------------------------------------------------
    print()
    print("Make ONE new column from column 26 with the alpha part when it has the form 'OVR01':")

    s.transformer = classify_data.Transform(26, '{prefix num.int}')
    new = s.new_columns()
    assert( new is False )
    assert( 'pattern' in s.transformer.errors )
    
    assert(len(s.transformer.components) == 2)
    pat = s.transformer.components[0]
    assert(pat._name == b'prefix')
    assert(pat._definition is None)
    pat._definition = b'[A-Z]+'

    new = s.new_columns()
    assert( new )
    assert( s.transformer.errors is None )

    print('*** pattern:', s.transformer._pattern._definition)
    print('*** components:', map23(lambda c: (c._name, c._definition), s.transformer.components))
    print('*** imports:', s.transformer.imports)
    

    print(new)


# -----------------------------------------------------------------------------
    print()
    print("TRANSFORM column 26 to extract the alpha prefix and the rest of the field:")

    s.transformer = classify_data.Transform(26, '{x .*}')
    s.set_transform_components()
    assert(len(s.transformer.components) == 1)
    # User enters defn for x
    pat = s.transformer.components[0]
    assert(pat._name == b'x')
    assert(pat._definition is None)
    pat._definition = b'[A-Z]+'

    new = s.new_columns()
    assert( new )
    assert( s.transformer.errors is None )

    print('*** pattern:', s.transformer._pattern._definition)
    print('*** components:', map23(lambda c: (c._name, c._definition), s.transformer.components))
    print('*** imports:', s.transformer.imports)
    
    print(new)

# -----------------------------------------------------------------------------

    print()
    print("TRANSFORM column 26 to extract the alpha prefix:")

    s.transformer = classify_data.Transform(26, 'x')
    s.set_transform_components()
    assert(len(s.transformer.components) == 1)
    # User enters defn for x
    pat = s.transformer.components[0]
    assert(pat._name == b'x')
    assert(pat._definition is None)
    pat._definition = b'[A-Z]+'
    # # User should not have to define '.'
    # pat = s.transformer.components[0]
    # assert(pat._name == b'.')
    # assert(pat._definition is None)
    # pat._definition = False

    new = s.new_columns()
    assert( new )
    assert( s.transformer.errors is None )

    print('*** pattern:', s.transformer._pattern._definition)
    print('*** components:', map23(lambda c: (c._name, c._definition), s.transformer.components))
    print('*** imports:', s.transformer.imports)
    
    print(new)

# -----------------------------------------------------------------------------
    print()
    print("** Experiment with find/findall on column 26 **")

    s.transformer = classify_data.Transform(26, '{find:[:digit:] n}')
    s.set_transform_components()
    print(map23(lambda p: (p._name, p._definition), s.transformer.components))
    
    assert(len(s.transformer.components) == 2)
    # User enters defn for n
    pat = s.transformer.components[0]
    assert(pat._name == b'n')
    assert(pat._definition is None)
    pat._definition = b'[:digit:]'

    new = s.new_columns()
    assert( new )
    assert( s.transformer.errors is None )

    print('*** pattern:', s.transformer._pattern._definition)
    print('*** components:', map23(lambda c: (c._name, c._definition), s.transformer.components))
    print('*** imports:', s.transformer.imports)
    
    print(new)


# ---------------------------------------------------------------------------------------------------
    print()
    print("Let's try to INFER a destructing for column 20")

    tr3, err = s.suggest_destructuring(20)
    assert( not tr3 )
    assert( not err )
    print('No suggested destructuring found, which was expected.')
    
# ---------------------------------------------------------------------------------------------------
    print()
    print("Let's try to INFER a destructing for column 25")

    tr3, err = s.suggest_destructuring(25)
    assert( tr3 )
    assert( not err )

    print()
    print("COMMIT the new cols above:")

    print('*** pattern:', tr3._pattern._definition)
    print('*** components:', map23(lambda c: (c._name, c._definition), tr3.components))
    print('*** imports:', tr3.imports)

    s.transformer = tr3
    s.commit_new_columns()

# ---------------------------------------------------------------------------------------------------
    print()
    print("Let's try to INFER a destructing for column 26 (+2 for previous commit)")

    s.transformer, err = s.suggest_destructuring(26+2)
    
    new = s.new_columns()

    assert( new )
    assert( s.transformer.errors is None )

    print('*** pattern:', s.transformer._pattern._definition)
    print('*** components:', map23(lambda c: (c._name, c._definition), s.transformer.components))
    print('*** imports:', s.transformer.imports)

    print(new)
    
    print()
    print("COMMIT the two cols above:")

    s.transformer = s.transformer
    s.commit_new_columns()

    # And we will make visible again the original column, 26, so we
    # can see in the final output that the destructuring worked
    # correctly:
    s.unhide_column(26)

    # Print to console
    classify_data.print_sample_data_verbosely(s, 0)

    filename, err = s.process_file()
    if not filename:
        print("Error generating output file!  Details:")
        print(err)
    else:
        print(filename)

# ---------------------------------------------------------------------------------------------------
    sys.exit(0)
# ---------------------------------------------------------------------------------------------------





# ---------------------------------------------------------------------------------------------------

test()

