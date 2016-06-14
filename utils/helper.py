"""helper.py

Helper functions.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import __future__
import ast
from config import logger_

def to_bool(arg):
    if arg.lower() in [ "0", "false", "no" ]:
        return False
    return True

def to_float(string):
    """Convert a given string to float """
    string = string.replace('"', '')
    return float(eval(string))

def get_ids( expr ):
    try:
        tree = ast.parse( expr )
    except Exception as e:
        logger_.warn( 'Expression not a valid python expression' )
        logger_.warn( '\t Expression was %s' % expr )
        logger_.warn( '\t Error during parsing %s' % e )
        return []
    ids = []
    for e in ast.walk( tree ):
        if isinstance( e, ast.Name ):
            ids.append( e.id )
    return ids


##
# @brief Eval the expression using python. The __future__ related compile flags
# make sure that 1/3 is reduced 0.33333 instead of 0.
#
# @param expr
#
# @return Reduced value as string whenever possible.
def reduce_expr( expr ):
    isReduced = 'false'
    try:
        val = eval(
                compile( expr , '<string>', 'eval',
                    __future__.division.compiler_flag )
                )
        isReduced = 'true'
    except Exception as e:
        logger_.debug( 'Failed to reduce %s' % expr )
        logger_.debug( '\tError was %s' % e )
        val = expr 
    return str(val), isReduced
