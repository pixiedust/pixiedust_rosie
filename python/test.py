# coding: utf-8
#  -*- Mode: Python; -*-                                              

from __future__ import unicode_literals, print_function

import sys, json, rosie, classify_data


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


def test():
    s = classify_data.Schema(datafile, samplesize)
    s.load_and_process()

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
    print("For demonstration purposes, we will delete columns 4 and 22-end...")
    s.hide_column(4)
    for i in range(22, s.cols):
        s.hide_column(i)

    print()
    classify_data.print_sample_data_verbosely(s, 0)

    print()
    classify_data.print_ambiguously_typed_columns(s)


    print()
    print(s.colnames)
    print(s.rosie_types)
    print(s.native_types)

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
    print("Now we change the native type of column 11 to complex:")
    s.set_native_type(11, complex)
    print(11, s.convert(11, '*FAIL*'))

    print()
    print("Make a new column based on column 26 to extract the numeric part:")
    new = s.new_columns(26, '{[^0-9]* n}', ['n'], 'n=[0-9]*')
    print(new)


    print()
    print("Make TWO new columns based on column 26 to extract the alpha prefix and the numeric part:")
    new = s.new_columns(26, '{prefix num.int}', ['prefix', 'num.int'], 'import num; prefix=[A-Z]+')
    print(new)

    print()
    print("COMMIT the two cols above:")
    new = s.commit_new_columns(26, '{prefix num.int}', ['prefix', 'num.int'], 'import num; prefix=[A-Z]+')
    classify_data.print_sample_data_verbosely(s, 0)

test()
