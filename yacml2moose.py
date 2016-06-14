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
import moose
import moose.print_utils as pu
import re
import ast
from utils import test_expr as te
from utils import expression as _expr
from utils import helper
import notify as warn
import config
from utils import typeclass as tc
import lxml.etree as etree
# from utils.helper import *
from collections import deque
logger_ = config.logger_



def helper_constant_propagation( text, reduced, unreduced ):
    # Get all identifiers which can be replaced.
    ids = helper.get_ids( text )
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
        elem.text, isReduced = helper.reduce_expr( elem.text ) 
        elem.attrib[ 'is_reduced' ] = isReduced
        return var_dict[var], True
    else:
        return var, False

def replace_variable_value( elem, local_vars, global_vars ):
    t = elem.text
    allDicts = list(local_vars) + list( global_vars )
    for i in helper.get_ids( elem.text ):
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

def init_compartment( compt_name, geometry_xml, model ):
    geomType = geometry_xml.attrib['shape']
    compt = None
    comptPath = '%s/%s' % ( model.path, compt_name )
    if geomType == 'cube':
        compt = moose.CubeMesh( comptPath )
        compt.volume = float(
                geometry_xml.xpath('variable[@name="volume"]')[0].text 
                )
    elif geomType == 'cylinder':
        compt = moose.CylMesh( comptPath )
        logger_.warn( 'Not fully supported yet. Need to attach geometry')
    else:
        compt = moose.CubeMesh( comptPath )
        compt.volume = float( 
                geometry_xml.xpath('variable[@name="volume"]')[0].text 
                )
        logger_.warn( 'Unsupported compartment type %s. Using cube' % geomType )
    return compt


def load_compartent( compt_xml, model ):
    # Load a given XML compartment into moose.
    logger_.info( 'Loading compartment into moose' )
    comptName = compt_xml.attrib['name']
    geometry = compt_xml.find( 'geometry' )
    compt = init_compartment( comptName, geometry, model )
    return compt

##
# @brief Replace other chemical species with x0, x1, x2 etc. Return the new
# expression along with a map.
#
# @param expr
#
# @return 
def rewrite_function_expression( expr ):
    ids = helper.get_ids( expr )
    replacePairs = []

    if 't' in ids: 
        ids.remove('t')

    for i, x in enumerate(set(ids)):
        found, replaceWith = x, 'x%s' % i
        expr = expr.replace( found, replaceWith )
        replacePairs.append( (found, replaceWith ) )
    return replacePairs, expr


##
# @brief Set concentration of a given Pool. If simple reduction to double is not
# possible, use moose.Function to set things up.
#
# @param pool
# @param pool_xml
#
# @return 
def set_pool_conc( pool, pool_xml, compt_path ):
    # Set pool properties.
    expr, isReduced = helper.reduce_expr(pool_xml.text)
    fieldName = pool_xml.attrib['name'].lower( )
    if isReduced == 'true':
        pool.setField( '%sInit' % fieldName, float(expr) )
        return pool

    # If not reduced to a simple float value, need a function to update the
    # concentrations etc.
    connections, expr = rewrite_function_expression( expr )
    f = moose.Function( '%s/func_set_%s' % ( pool.path, fieldName ) )
    f.expr = expr 
    # f.mode = 1
    for i, (x, y) in enumerate( connections ):
        poolpath = '%s/%s' % ( compt_path, x )
        assert moose.exists( poolpath )
        moose.connect( poolpath, '%sOut' % fieldName, f.x[i], 'input' )

    try:
        toSet = 'set%s%s' % ( fieldName[0].upper(), fieldName[1:] )
        moose.connect( f, 'valueOut', pool, toSet )
    except Exception as e:
        logger_.error( "I cannot set this expression " )
        logger_.error( "\t The expr was %s" % expr )
        logger_.error( "\t The error was %s" % e )

def load_species( species_xml, root_path ):
    speciesPath = '%s/%s' % ( root_path, species_xml.attrib['name'] )
    logger_.debug( 'Creating Pool/BufPool, path=%s' % speciesPath )
    if species_xml.attrib.get('is_buffered', 'false' ) == 'true':
        pool = moose.BufPool( speciesPath )
    else:
        pool = moose.Pool( speciesPath )

    params = species_xml.xpath( 'parameter' )
    assert params, 'Need at least N or conc field'
    for p in params:
        if p.attrib['name'].lower() in [ 'n', 'conc' ]:
            set_pool_conc( pool, p, root_path )
    return p


def load_chemical_reactions_in_compartment( subnetwork, compt ):
    logger_.info( 'Loading chemical reaction network in compartment %s' % compt )
    netPath = '%s/%s' % ( compt.path, subnetwork.attrib['name'] )
    moose.Neutral( netPath )
    [ load_species( c, netPath ) for c in subnetwork.xpath('species' ) ]


def load_xml( xml ):
    # First get all the compartments and create them.
    modelname = xml.find('model').attrib['name']
    moose.Neutral( '/yacml' )
    model = moose.Neutral( '/yacml/%s' % modelname )
    compts = {}
    for c in xml.xpath( '/yacml/model/compartment' ):
        compts[c.attrib['name'] ] = compt = load_compartent( c, model )
        [ load_chemical_reactions_in_compartment( x, compt )
                for x in c.xpath( 'chemical_reaction_subnetwork' )
                ]
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
