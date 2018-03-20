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
    s = classify_data.load_sample_data(datafile, samplesize)
    s.process_sample_data()

    print("\nData has", s.cols, "columns, and sample set has", len(s.sample_data), "rows")
    print()

    for removed_row in s.inconsistent_rows:
        i, row = removed_row
        if len(row) > s.cols:
            print("row", i, "has too many columns", s.sample_data[i])
        else:
            print("row", i, "has too few columns", s.sample_data[i])

    print()
    print("In a sample of", samplesize, "rows, we excluded", len(s.inconsistent_rows),
          "rows which did not have the expected number of columns.")

    print()
    print("For demonstration purposes, we will delete column 4...")
    s.hide_column(4)

    print()
    classify_data.print_sample_data_verbosely(s, 0)

    print()
    classify_data.print_ambiguously_typed_columns(s)


    print()
    print(s.colnames)
    print(s.rosie_types)
    print(s.native_types)

    print()
    for i in range(4, s.cols):
        s.hide_column(i)

    print("Sample data with visible columns only")
    for row in s.sample_data:
        visible = [datum for i, datum in enumerate(row) if s.colmask[i]]
        print(visible)


test()
