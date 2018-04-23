#  -*- coding: utf-8; -*-
#  -*- Mode: Python; -*-                                              
# 
#  destructure.py
# 
#  © Copyright IBM Corporation 2018.
#  LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
#  AUTHOR: Jamie A. Jennings

from __future__ import unicode_literals, print_function
from adapt23 import *
import rosie_matcher

separators = set({'comma', 'semicolon', 'dash', 'slash', 'find.*'})

def fields(match_subs):
    return list(map(lambda s: s['data'],
                    [ sub for sub in match_subs
                      if (sub['type'] not in separators and (sub['type'] != 'rest' or sub['data'] != '')) ] ))

def compile(matcher):
    assert( isinstance(matcher, rosie_matcher.Matcher) )
    matcher.load(rpl)
    return matcher.compile('destructure.tryall')

def match(pat, matcher, datum):
    m = matcher.match(pat, datum.strip())
    if not m: return None
    key = rosie_matcher.most_specific(m)
    return key, key['subs']

rpl = b'''
-- -*- Mode: rpl; -*-                                                                                   
--
-- destructure.rpl
--
-- © Copyright Jamie A. Jennings 2018.
-- LICENSE: MIT License (https://opensource.org/licenses/mit-license.html)
-- AUTHOR: Jamie A. Jennings

package destructure

term = [)}\]]		 -- termination pattern is closing paren/brack/brace
rest = {!term .}*

local dash = "-"
local slash = "/"
local comma = ","
local semicolon = ";"

dashes = {{keepto:>{term / dash} dash}+ rest}
slashes = {{keepto:>{term / slash} slash}+ rest}
commas = {{keepto:>{term / comma} comma}+ rest}
semicolons = {{keepto:>{term / semicolon} semicolon}+ rest}

-- test dashes accepts "-", "--", "-l", "i--"
-- test dashes rejects "", "abcdef"

-- test dashes accepts "12-13-14-dog-cat", "en-US", "en-CA", "en-GB"
-- test slashes accepts "3/25/2018", "4/5", "XX/XY", "/r"
-- test commas accepts "Detroit, MI, U.S."
-- test semicolons accepts "145;32;NJ", ";", "48K;"

local alpha = [:alpha:]+ 
local num = [:digit:]+
alphanum = { {alpha num}+ alpha? } rest
numalpha = { {num alpha}+ num? } rest

-- test alphanum accepts "A3", "ABC0", "BLDG501", "WD40", "A2N1"
-- test alphanum rejects "", "A", "123ABC"
-- test numalpha accepts "3A", "01ABC", "123ABC", "501C", "1B12"
-- test numalpha rejects "", "A", "6", "A3"

-- sep looks for a separator character, trying several in turn
alias sep = dashes / slashes / commas / semicolons
-- abbrev looks for interleaved sequences of alphabetic and numeric characters,
-- with no whitespace between them, such as might be found in an abbreviation
alias abbrev = alphanum / numalpha

-- test sep includes dashes "WD-40"
-- test abbrev accepts "123DEF", "A10", "1B12"
-- test abbrev rejects "WD-40"

parentheses = { "(" (sep / abbrev / rest) ")" / error:#"missing_close" }
brackets =    { "[" (sep / abbrev / rest) "]" / error:#"missing_close" }
braces =      { "{" (sep / abbrev / rest) "}" / error:#"missing_close" }

alias tryall = parentheses /
	       brackets /
	       braces /
	       {sep (term error:#missing_open)? } /
	       abbrev

-- test tryall includes dashes "WD-40"
-- test tryall accepts "123DEF", "A10", "1B12"
-- test tryall accepts "123-DEF", "A/10", "1B12; hello world;"
-- test tryall excludes alphanum "WD-40"
-- test tryall accepts "(123ABC)", "(4.77, 1)", "{foo, bar, baz}"
-- test tryall includes parentheses "(abc-123-def)", "()"
-- test tryall includes brackets "[4.77, 1, 2.3]", "[1]", "[]"
-- test tryall accepts "(abc-123-def)", "[4.77, 1, 2.3]"

-- NOTE the asymmetry in the output, depending on whether there was an opening
-- delimeter and no closing one, or vice versa:
-- 
-- test tryall includes parentheses "(abc-123-def"
-- test tryall includes error "(abc-123-def"
-- test tryall excludes brackets "1, 2, 3]"
-- test tryall includes commas "1, 2, 3]"
-- test tryall includes term "1, 2, 3]"
-- test tryall includes error "1, 2, 3]"


'''
