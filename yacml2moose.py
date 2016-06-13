"""yacml2moose.py

Load YACML model into MOOSE simulator.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


import __future__
import networkx.drawing.nx_agraph as nxAG
import moose
import moose.print_utils as pu
import moose.utils as mu
import re
import ast
from utils import test_expr as te
from utils import expression as _expr
import notify as warn
import config
from utils import typeclass as tc
import lxml.etree as etree
# from utils.helper import *
from collections import deque
logger_ = config.logger_


def get_ids( expr ):
    try:
        tree = ast.parse( expr )
    except Exception as e:
        logger_.warn( 'Expression not a valid python expression' )
        logger_.warn( '\t Expression was %s' % expr )
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
# @return Reduced value as string.
def eval_expr( expr ):
    try:
        val = eval( compile( expr ), '<string>'
                , 'eval', __future__.division.compile_flags 
                )
    except Exception as e:
        val = expr 
    return str(val)


def helper_constant_propagation( text, reduced, unreduced ):
    # Get all identifiers which can be replaced.
    ids = get_ids( text )
    newText = text
    for iden in ids:
        # replace from the unreduced first.
        if iden in unreduced:
            logger_.debug( '== Replacing %s' % iden )
            newText = newText.replace( iden, unreduced[iden] )
        elif iden in reduced:
            logger_.debug( '== Replacing %s' % iden )
            newText = newText.replace( iden, reduced[iden] )
    
    # If no more changes are possible, return the result else call the function
    # recusively.
    if newText == text:
        return text
    else:
        return helper_constant_propagation( newText, reduced, unreduced )

def get_global_variables( elem, reduced = {}, unreduced = {} ):
    # Get the compartwarn geometry paramters.
    while elem.getparent() is not None:
        elem = elem.getparent()
        ur, r = get_local_variables( elem )
        reduced.update( r )
        unreduced.update( ur )
    return (unreduced, reduced) 

def get_local_variables( elem ):
    variables = {}
    reduced, unreduced = {}, {}
    for v in  elem.xpath( 'variable[@is_reduced="true"]' ):
        reduced[v.attrib['name'] ] = v.text
    for v in  elem.xpath( 'variable[@is_reduced="false"]' ):
        unreduced[v.attrib['name'] ] = v.text
    return (unreduced, reduced) 

def replace_variable_value_from_dict( elem, var, var_dict ):
    if var in var_dict:
        elem.text = elem.text.replace(var, var_dict[var] )
        try:
            elem.text = eval_expr( elem.text ) 
            elem.attrib[ 'is_reduced' ] = 'true'
        except Exception as e:
            pass
        return var_dict[var], True
    else:
        return var, False

def replace_variable_value( elem, local_vars, global_vars ):
    t = elem.text
    allDicts = list(local_vars) + list( global_vars )
    for i in get_ids( elem.text ):
        # Replace from each dictionary in order, stop at first replacement.
        for d in allDicts:
            if replace_variable_value_from_dict( elem, i, d )[1]:
                break

    if t == elem.text:
        return elem
    else:
        return replace_variable_value( elem, local_vars, global_vars )


def do_constant_propagation_on_elem( elem ):
    validElems = [ 'variable', 'reaction', 'species' ]
    # if elem.tag not in validElems:
        # return

    if elem.attrib.get('is_reduced', 'false') == 'true':
        return

    globalVars = get_global_variables( elem )
    localVars = get_local_variables( elem )
    if elem.tag in [ 'variable', 'parameter' ]:
        # A variable may refer to another variable in its expression. It may
        # also refer to another global variable.
        logger_.debug( 'Global variable  %s = %s' % ( elem.attrib['name'], globalVars ))
        logger_.debug( 'Local variable %s = %s' % ( elem.attrib['name'], localVars )) 
        elem = replace_variable_value( elem, localVars, globalVars )

##
# @brief Do the constant propagation recursively.
#
# @param tree
#
# @return 
def do_constant_propagation( tree ):
    listOfElems = []
    queue = deque( [ tree ] )
    while queue:
        el = queue.popleft() 
        listOfElems.append( el )
        queue.extend( el )          # Append el children
        
    # Now pop elements at the back from the listOfElems and start propagating
    # constant.
    while listOfElems:
        elem = listOfElems.pop( )
        do_constant_propagation_on_elem( elem )

def load_xml( xml ):
    # First get all the compartments and create them.
    for c in xml.xpath( '/yacml/model/compartment' ):
        print c

    quit( )

##
# @brief Load yacml XML model into MOOSE.
#
# @param xml Input model AST in XML.
#
# @return  Root path of model in MOOSE, /yacml.
def load( xml ):
    # Before loading AST xml into MOOSE, replace each variable by its value
    # whenever posiible.
    do_constant_propagation( xml )
    load_xml( xml )
    outfile = '/tmp/yacml.xml' 
    with open( outfile, 'w' ) as f:
        f.write( etree.tostring( xml, pretty_print = True ) )
    logger_.debug( '[INFO] Flattened xml is written to %s' % outfile )
    return xml
