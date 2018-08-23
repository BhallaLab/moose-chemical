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
import re
import math
import moose

# Bring imports from math to global namespace so that eval can use them.
from math import *
from config import logger_

funcs = list(math.__dict__.keys()) + [ 'fmod', 'rand', 'rand2' ]

def to_bool(arg):
    if arg.lower() in [ "0", "false", "no" ]:
        return False
    return True

def get_ids( expr ):
    # The expression might also have ite-expression of muparser.
    itePat = re.compile( r'(.+?)\?(.+?)\:(.+)' )
    m = itePat.match( expr )
    if m:
        exprs = m.group(1, 2, 3)
    else:
        exprs = [ expr ]

    ids = []
    for expr in exprs:
        try:
            tree = ast.parse( expr )
        except Exception as e:
            logger_.warn( 'Expression not a valid python expression' )
            logger_.warn( '\t Expression was %s' % expr )
            logger_.warn( '\t Error during parsing %s' % e )
            return []
        for e in ast.walk( tree ):
            if isinstance( e, ast.Name ):
                if e.id not in funcs:
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
        # logger_.debug( 'Failed to reduce %s' % expr )
        # logger_.debug( '\tError was %s' % e )
        val = expr 
    return str(val), isReduced

def to_float( expr ):
    val, isReduced = reduce_expr( expr )
    if isReduced:
        return float(val)
    else:
        raise RuntimeError( 'Failed to convert to float : %s' % expr )

def compt_info( compt ):
    """Get the compartment info as string"""
    info = ''
    if isinstance( compt, moose.CubeMesh ):
        info += 'Cube\n'
        info += '\tx0, y0, z0 : %s, %s, %s\n' % (compt.x0, compt.y0, compt.z0)
        info += '\tx1, y1, z1 : %s, %s, %s\n' % (compt.x1, compt.y1, compt.z1)
        info += '\tvolume : %s' % compt.volume 
    elif isinstance( compt, moose.CylMesh ):
        info += 'Cylinder:\n'
        info += '\tr0, r1 : %s, %s\n' % (compt.r0, compt.r1 )
        info += '\tx0, y0, z0 : %s, %s, %s\n' % (compt.x0, compt.y0, compt.z0 )
        info += '\tx1, y1, z1 : %s, %s, %s\n' % (compt.x1, compt.y1, compt.z1 )
        try:
            info ++ '\tvolume = %s' % compt.volume 
        except Exception as e:
            pass
    else:
        info += "Unknown/unsupported compartment type %s" % compt
    return info

def pool_info( pool ):
    info = ''
    info += ' n0 = %f,' % pool.nInit 
    info += ' n =  %s,' % pool.n 
    info += ' diffConst = %s,' % pool.diffConst 
    return info
