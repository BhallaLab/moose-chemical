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
import re
import ast
import math 

import config
import lxml.etree as etree
import moose.print_utils as pu
import utils.xml as xml

from utils import test_expr as te
from utils import helper

from collections import deque

logger_ = config.logger_

logger_.debug( 'Using moose from %s' % moose.__file__ )
logger_.debug( '| Version %s' % moose.__version__ )

# Some more global variables such as volume of compartment, length and radius.
globals_ = { }
modelname_ = None

# Required to construct a unique name for moose.Tables
current_chemical_subnetwork_name_ = None

moose_dict_ = { 
        'kb' : 'Kb' , 'kf' : 'Kf' 
        }

# Store all moose.Table in dictionary: path : object
tables_ = { }
def helper_constant_propagation( text, reduced, unreduced ):
    # Get all identifiers which can be replaced.
    ids = helper.get_ids( text )
    newText = text
    for iden in ids:
        # replace from the unreduced first.
        if iden in unreduced:
            logger_.debug( '|| Replacing %s' % iden )
            newText = newText.replace( iden, unreduced[iden] )
        elif iden in reduced:
            logger_.debug( '|| Replacing %s' % iden )
            newText = newText.replace( iden, reduced[iden] )
    
    # If no more changes are possible, return the result else call the function
    # recusively.
    if newText == text:
        return text
    else:
        return helper_constant_propagation( newText, reduced, unreduced )

def get_global_variables( elem, reduced = {}, unreduced = {} ):
    # Get the compartwarn geometry paramters.
    global globals_
    while elem.getparent() is not None:
        elem = elem.getparent()
        ur, r = get_local_variables( elem )
        reduced.update( r )
        unreduced.update( ur )

    reduced.update( globals_ )
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
    allVars = local_vars + global_vars
    for i in helper.get_ids( elem.text ):
        # Replace from each dictionary in order, stop at first replacement.
        for varDict in allVars:
            if replace_variable_value_from_dict( elem, i, varDict )[1]:
                break

    if t == elem.text:
        return elem
    else:
        return replace_variable_value( elem, local_vars, global_vars )


def do_constant_propagation_on_elem( elem ):
    validElems = [ 'variable', 'reaction', 'species' ]
    if elem.attrib.get('is_reduced', 'false') == 'true':
        return

    # Tuple of ordered and unorderd variables as dictionary
    globalVars = get_global_variables( elem )
    localVars = get_local_variables( elem )
    if elem.tag in [ 'variable', 'parameter' ]:
        # A variable may refer to another variable in its expression. It may
        # also refer to another global variable.
        # logger_.debug( 'Global variable  %s = %s' % ( elem.attrib['name'], globalVars ))
        # logger_.debug( 'Local variable %s = %s' % ( elem.attrib['name'], localVars )) 
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
    global globals_
    geomType = geometry_xml.attrib['shape']
    compt, volume = None, 0.0
    comptPath = '%s/%s' % ( model.path, compt_name )
    if geomType == 'cube':
        compt = moose.CubeMesh( comptPath )
        compt.volume = xml.get_value_from_parameter_xml( geometry_xml, 'volume' )
        volume = compt.volume
    elif geomType == 'cylinder':
        compt = moose.CylMesh( comptPath )
        compt.x0, compt.y0, compt.z0 = 0, 0, 0
        compt.x1 = xml.get_value_from_parameter_xml( geometry_xml, 'length' )
        compt.y1, compt.z1 = compt.y0, compt.z0
        compt.r0 = compt.r1 = xml.get_value_from_parameter_xml( geometry_xml, 'radius' )
        volume = xml.get_value_from_parameter_xml( geometry_xml, 'volume' )
        compt.volume = volume
    else:
        compt = moose.CubeMesh( comptPath )
        compt.volume = xml.get_value_from_parameter_xml( geometry_xml, 'volume' )
        volume = compt.volume
        logger_.warn( 'Unsupported compartment type %s. Using cube' % geomType )
    logger_.debug( '|| Added compartment\n\t %s' % helper.compt_info( compt ) )
    assert volume > 0, "Volume of compartment must be > 0.0 "
    globals_['volume'] = volume
    return compt

def load_compartent( compt_xml, model ):
    # Load a given XML compartment into moose.
    logger_.info( 'Loading compartment into moose' )
    comptName = compt_xml.attrib['name']
    geometry = compt_xml.find( 'geometry' )
    assert geometry is not None, "Need geometry information"
    compt = init_compartment( comptName, geometry, model )
    return compt

##
# @brief Replace other chemical species with x0, x1, x2 etc. Return the new
# expression along with a map. Make sure global keyword such as volume, t does
# not get confused with Pools.
#
# @param expr
#
# @return 
def rewrite_function_expression( expr ):
    global globals_
    allIds = helper.get_ids( expr )
    replacePairs = []
    ids = set()
    ignoreIds = [ 't' ] + globals_.keys()

    for i in allIds:
        if i not in ignoreIds:
            ids.add( i )
        elif i in globals_.keys():
            expr = expr.replace( i, str(globals_[i]) )

    for i, x in enumerate(ids):
        found, replaceWith = x, 'x%s' % i
        expr = expr.replace( found, replaceWith )
        replacePairs.append( (found, replaceWith ) )
    return replacePairs, expr

def attach_parateter_to_reac( param, reac, chem_net_path ):
    fieldName = param.attrib[ 'name' ]
    fieldName = moose_dict_.get( fieldName, fieldName )
    if param.attrib[ 'is_reduced' ] == 'true':
        reac.setField( fieldName, float( param.text ) )
        logger_.debug( 
                '|| Parameter %s.%s=%s' % (reac.path, fieldName, param.text)
                )
    else:
        f = moose.Function( '%s/set_%s' % ( reac.path, fieldName ) )
        connections, expr = rewrite_function_expression( param.text )
        f.x.num = len( connections )
        for i, (x, y) in enumerate( connections ):
            mooseElem = moose.element( '%s/%s' % ( chem_net_path, x ) )
            if fieldName.lower() in [ 'numkf', 'numkb' ]:
                moose.connect( mooseElem, 'nOut', f.x[i], 'input' )
            else:
                moose.connect( mooseElem, 'concOut', f.x[i], 'input' )
        f.expr = expr
        reacF = 'set' + fieldName[0].upper() + fieldName[1:]
        logger_.debug(
                '|| Parameter (expr) %s.%s = %s' % ( reac.path, reacF, f.expr )
                )
        moose.connect( f, 'valueOut', reac, reacF )

def attach_table_to_species( moose_pool, field_name ):
    """Create a moose.Table to read the field_name 
    """
    global tables_
    global current_chemical_subnetwork_name_
    tabPath = '%s/table_%s' % (moose_pool.path, field_name ) 
    tab = moose.Table2( tabPath )
    logger_.info( 'Created %s' % tab )
    tab.name = '%s.%s.%s' % ( current_chemical_subnetwork_name_
            , moose_pool.name
            , field_name 
            )
    getField = 'get' + field_name[0].upper() + field_name[1:]
    try:
        moose.connect( tab, 'requestOut', moose_pool, getField )
        tables_[ tabPath ] = tab
    except Exception as e:
        logger_.warn( 'Failed to add a Table on %s.%s' % ( moose_pool.path,
            field_name )
            )
        logger_.warn( '\tError was %s' % e )

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
        logger_.debug( 
                '|| Set field %s = %s' % (
                    fieldName, pool.getField( '%sInit' % fieldName ) )
                )
        return pool

    # If not reduced to a simple float value, need a function to update the
    # concentrations etc.
    connections, expr = rewrite_function_expression( expr )
    f = moose.Function( '%s/func_set_%s' % ( pool.path, fieldName ) )
    f.expr = expr 
    f.x.num = len( connections )
    for i, (x, y) in enumerate( connections ):
        poolpath = '%s/%s' % ( compt_path, x )
        assert moose.exists( poolpath ), '%s does not exists' % poolpath
        moose.connect( poolpath, '%sOut' % fieldName, f.x[i], 'input' )
        logger_.debug( 
                '||| Connecting %s.%s to function input' % ( poolpath, fieldName )
            )
    try:
        toSet = 'set%s%s' % ( fieldName[0].upper(), fieldName[1:] )
        moose.connect( f, 'valueOut', pool, toSet )
        logger_.debug( '\tSet field %s = %s' % ( toSet, f.expr) )
    except Exception as e:
        logger_.error( "I cannot use this expression on Function" )
        logger_.error( "\t The expr was %s" % expr )
        logger_.error( "\t The error was %s" % e )

def load_species( species_xml, root_path ):
    """Load a species XML into MOOSE under root_path 

         root_path is the path of recipe instantiation.
    """
    global current_chemical_subnetwork_name_
    speciesPath = '%s/%s' % ( root_path, species_xml.attrib['name'] )

    # This is neccessary to construct unique names for tables.
    current_chemical_subnetwork_name_ = root_path.split('/')[-1]


    if species_xml.attrib.get('is_buffered', 'false' ) == 'true':
        pool = moose.BufPool( speciesPath )
    else:
        pool = moose.Pool( speciesPath )

    logger_.info( 'Created %s' % pool )
    if 'diffusion_constant' in species_xml.attrib:
        pool.diffConst = helper.to_float( species_xml.attrib['diffusion_constant'] )
        logger_.debug( '\tDiffusion const = %s' % pool.diffConst )

    params = species_xml.xpath( 'parameter' )
    assert params, 'Need at least N or conc field'
    for p in params:
        if p.attrib['name'].lower() in [ 'n', 'conc' ]:
            set_pool_conc( pool, p, root_path )

    recordElem = species_xml.xpath( 'variable[@name="record"]' )
    if recordElem:
        attach_table_to_species( pool, recordElem[0].text )
    return p

def load_reaction( reac_xml, chem_net_path ):
    logger_.info( 'Loading reaction %s' % reac_xml.attrib['name'] )
    instOf  = reac_xml.attrib.get( 'instance_of', None )
    reacPath = '%s/%s' % ( chem_net_path, reac_xml.attrib['name'] )
    r = moose.Reac( reacPath )
    for sub in reac_xml.xpath( 'substrate' ):
        subName = sub.text
        subPool = moose.element( '%s/%s' % (chem_net_path, subName ) ) 
        for i in range( int( sub.attrib['stoichiometric_number']) ):
            logger_.debug( '|| Adding subtrate %s' % subPool.path )
            moose.connect( r, 'sub', subPool, 'reac' )
    for prd in reac_xml.xpath( 'product' ):
        prdName = prd.text
        prdPool = moose.element( '%s/%s' % (chem_net_path, prdName ) ) 
        for i in range( int( prd.attrib['stoichiometric_number']) ):
            logger_.debug( '|| Adding product  %s' % prdPool.path )
            moose.connect( r, 'prd', prdPool, 'reac' )
    if instOf:
        rInst = xml.find_reaction_instance( reac_xml.getparent(), instOf )
        params = rInst.xpath( 'parameter' )
    else:
        params = reac_xml.xpath( 'parameter' )

    assert len(params) > 1, "Need at least kf/kb, numKf/numKb"
    [ attach_parateter_to_reac( p, r, chem_net_path ) for p in params ]

def setup_solver( compt_xml, compt ):
    """Setup solver in each compartment.

    """
    logger_.info( "Setting up solver in compartment %s" % compt.path )
    st = moose.Stoich( '%s/stoich' % compt.path )
    if compt_xml.attrib['type'] == "stochastic":
        logger_.info( '\tAdded stochastic solver' )
        s = moose.Gsolve( '%s/gsolve' % st.path )
        # This is essential otherwise the stimulus will not be computed.
        s.useClockedUpdate = True
    else:
        s = moose.Ksolve( '%s/ksolve' % st.path )
        logger_.info( '\tAdded deterministic solver' )

    st.compartment = compt
    st.ksolve = s

    # Enable diffusion in compartment.
    diffusion = compt_xml.xpath( 'variable[@name="diffusion_length"]' )
    if diffusion:
        dsolve = moose.Dsolve( '%s/dsolve' % st.path )
        st.dsolve = dsolve
        logger_.info( '\tEnabled diffusion in compartment' )
        try:
            compt.diffLength = float( diffusion[0].text )
            logger_.info( '\t\tdiffLength is set to %s' % compt.diffLength )
        except Exception as e:
            logger_.warn( 
                    'Compartment %s does not support paramter diffLength' %
                    compt )

    st.path = "%s/##" % compt.path
    logger_.debug( '|| Set solver path = %s' % st.path )

def setup_recorder( ):
    """Setup a moose.Streamer to store all tables into one file.
    """
    global tables_
    streamer = moose.Streamer( '/yacml/streamer' )
    streamer.addTables( tables_.values( ) )
    return streamer

def load_chemical_reactions_in_compartment( subnetwork, compt ):
    logger_.info( 'Loading chemical reaction network in compartment %s' % compt )
    netPath = '%s/%s' % ( compt.path, subnetwork.attrib['name'] )
    moose.Neutral( netPath )
    [ load_species( c, netPath ) for c in subnetwork.xpath('species' ) ]
    [ load_reaction( r, netPath ) for r in subnetwork.xpath('reaction') ]

def setup_run( sim_xml, streamer = None ):
    global modelname_
    simTime = helper.to_float( sim_xml.attrib['sim_time'] )
    logger_.info( 'Running MOOSE for %s seconds' % simTime )
    if sim_xml.attrib.get('format') is not None:
        format_ = sim_xml.attrib[ 'format' ]
    else:
        format_ = 'csv'
    streamer.outfile = '%s.%s' %  ( modelname_, format_ )
    logger_.info( 'Saving streamer file to %s' % streamer.outfile )

    # If plot_dt is defined, use it. Only effective on moose.Table2.
    # By default it is per 1 seconds.
    if sim_xml.attrib.get( 'record_dt', False ):
        moose.setClock( 18, helper.to_float( sim_xml.attrib['record_dt' ] ) )
        logger_.debug( "|| Set dt of moose.Table2 = %s" % sim_xml.attrib['record_dt'] )

    moose.reinit( )
    moose.start( simTime, 1 )

def load_xml( xml ):
    """Load a given YACML AST in XML format into MOOSE.
    Return moose.Tables with data.
    """
    # First get all the compartments and create them.
    global tables_
    global modelname_
    modelname_ = xml.find('model').attrib['name']
    moose.Neutral( '/yacml' )
    model = moose.Neutral( '/yacml/%s' % modelname_ )
    compts = {}
    for c in xml.xpath( '/yacml/model/compartment' ):
        compts[c.attrib['name'] ] = compt = load_compartent( c, model )
        for x in c.xpath( 'chemical_reaction_subnetwork' ):
            load_chemical_reactions_in_compartment( x, compt )
        setup_solver( c, compt )
    st = setup_recorder( )

    simulator = xml.xpath( '/yacml/model/simulator' )
    if simulator:
        setup_run( simulator[0], st )
    return tables_

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
    logger_.info( '[INFO] Flattened xml is written to %s' % outfile )
    return xml
