"""pre_processor.py: 

Given a graph, replace its expressions on nodes.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

from config import logger_
import expression
import re
import parser
import ast
import networkx as nx
from math import *

# These are the keys which will/might have a complicated expression on them.
keys_with_expressions_ = [ 'kf', 'kb', 'numKf', 'numKb', 'N', 'conc',
        'diffusion_constant' ]
global_expr_g_ = nx.DiGraph( )
globals_ = None

def get_identifiers( syntax_tree ):
    idents = set()
    for n in ast.walk( syntax_tree ):
        if isinstance( n, ast.Name ):
            idents.add(n.id)
        else:
            pass
    return idents

def build_ast( expr ):
    st = None
    try:
        st = ast.parse( str(expr) )
    except Exception as e:
        logger_.debug("Could not build AST out of expression= %s" % expr)
        logger_.debug("\tError : %s" % e)
    return st

def pre_process_node( node, network ):
    """Pre-process each node """
    attrs = network.node[node]
    for k, v in attrs.items():
        try:
            attrs[key] = eval(v)
        except Exception as e:
            logger_.debug("Expression %s is not a simple python expression" % v)
            continue 
    return attrs

def reduce_expr( expr ):
    """reduce_expr Reduce a given expression if possible. Return (reduced expr,
    True) if reduction was successful, (old expression, False) is unsuccessful.

    :param expr: String, Expression to be reduced.
    """
    try:
        newExpr = str( eval( expr ) )
        return newExpr, True
    except NameError as e:
        return expr, False
    except Exception as e:
        logger_.warn("Unknown error in expr: %s" % expr)
    return expr, False


def build_global_expression_graph( network ):
    """build_global_expression_graph

    :param network:
    """
    global_expr_ = network.graph['graph']
    global global_expr_g_

    for k, v in global_expr_.items():
        global_expr_g_.add_node(k, expr = v)

    for k, v in global_expr_.items():
        st = build_ast( v )
        if st is None:
            continue
        if reduce_expr(v)[1]:
            # if this expression can be evaluated, compute its value and attach
            # it.
            global_expr_g_.add_node(k, reduced = reduce_expr(v)[0] )
        else:
            # If not then it must depends on other expressions.
            otherVars = get_identifiers( st )
            logger_.debug("Expr of %s depends on %s" % (k, otherVars))
            for v in otherVars:
                global_expr_g_.add_edge(k, v)
    # logger_.debug("Global variables: %s" % global_expr_g_.nodes())
    return global_expr_g_

def flatten_global_expressions( network ):
    global global_expr_g_ 
    g = global_expr_g_
    for x in nx.dfs_postorder_nodes( g ):
        logger_.debug("Trying to reduce expression on node %s" % x)
        if 'expr' not in g.node[x]:
            logger_.debug("Node %s does not have any expr" % x)
            logger_.debug("Not doing anything.")
        else:
            expr = flatten_expression_on_node(x, g )
            # update the value global variables.
            if x in network.graph['graph']:
                network.graph['graph'][x] = expr
    return True

def flatten_expression_on_node( x, g ):
    """Flatten expression on given node x of graph g """
    expr = g.node[x]['expr']
    msg = "NODE %s, EXPR=%s" % (x, expr)
    if g.node[x].get('reduced', ''):
        logger_.debug("|NODE %s| Expression on node is already reduced" % x)
        logger_.debug("   to %s" % g.node[x]['reduced'] )
        return g.node[x]['reduced']

    for xx in g.successors(x):
        logger_.debug( "%s <== %s" % (x , xx ) )
        # If this successor already has a reduced expression then
        # replace it with its value.
        expr = g.node[x]['expr']
        if 'reduced' in g.node[xx]:
            logger_.debug("replacing %s with %s" % (xx, g.node[xx]['reduced']))
            g.node[x]['expr'] = expr.replace(xx, g.node[xx]['reduced'])
        elif 'expr' in g.node[xx]:
            g.node[x]['expr'] = expr.replace(xx, g.node[xx]['expr'])
        else:
            continue
    # After all substitutions, try to reduce the expression.
    g.node[x]['reduced'] = reduce_expr( g.node[x].get('expr') )[0]
    msg += ", REDUCED= %s" % (g.node[x].get('reduced'))
    logger_.info( msg )
    return g.node[x]['reduced']


def reduce_node_expr( n, network):
    """reduce_node_expr Reduce the expression on network node. Replace local

    :param n: The node of network currently being processed.
    :param network: Whole network.
    """

    global keys_with_expressions_ 
    global globals_

    attr = network.node[n]
    # Create the expression graph.
    expG = nx.DiGraph( )
    for k, v in attr.items():
        expG.add_node(k, expr = v )
        
    for k, v in attr.items():
        st = build_ast( v )
        if st is None:
            continue
        if reduce_expr(v)[1]:
            expG.node[k]['reduced'] =  reduce_expr(v)[0] 
        for d in get_identifiers( st ):
            expG.add_edge( k, d )

    # Once the dependencies graph is build, we need to reduce it.
    for x in nx.dfs_postorder_nodes( expG ):
        # If its expr is not available locally, look-up in global graph. If we
        # don't find it in global also, then  it must be another node.
        if 'expr' not in expG.node[x]:
            if x in globals_: 
                # Copy its value from globals.
                expG.node[x]['expr'] = globals_[x]
            elif x in network.nodes():
                # x is another node in network. Its expression is itself.
                expG.node[x]['expr'] = x
            else: pass

        # By now we might have an expression on this node. If not, then we just
        # continue. 
        if 'expr' in expG.node[x]:
            expr = expG.node[x]['expr']
            for xx in expG.successors(x):
                if 'expr' in expG.node[xx]:
                    expr = expr.replace( xx, expG.node[xx]['expr'] )
                else: pass
                expG.node[x]['expr'] = reduce_expr( expr )[0]

            # Now only if this key is in keys_with_expressions_ list, then only
            # reduce it. Put the reduced expression into node attribute.
            if x in keys_with_expressions_:
                newExpr = reduce_expr( expr )[0]
                attr[x] = newExpr
                logger_.debug( '@node %s, reduced expr = %s' % (x, newExpr) )
        else:
            logger_.debug( "No expression found for node %s, %s" % (x,
                expG.node[x]))


def reduce_key_val_on_node( key, val, expr_graph, network):
    """reduce_key_val_on_node Reduce the key=value to key=new_val where new_val
    is computed by substituting variables.

    :param key:
    :param val:
    :param expr_graph:
    :param network:
    """

    global global_expr_g_
    if key not in keys_with_expressions_:
        return val

    st = None
    try:
        st = ast.parse( val )
    except SyntaxError as e:
        logger_.warn("Expr %s=%s is malformed" % (key, val))
        logger_.warn("... Ignoring. ")
        return val

    assert st, "If we are here we must have parsed the expression to ast"
    msg = '|KEY %s| OLD expr = %s' % (key, val)
    if not reduce_expr( val )[1]:
        # It can't be reduced. Don't change it.
        otherVars = get_identifiers( st )
        for v in otherVars:
            if v in local_vars:
                logger_.debug("Found replacement in locals")
                newVal = local_vars[v]
                logger_.debug("Replacing %s with %s" % (v, newVal))
                val = val.replace(v, newVal)
            elif v in network.graph['graph']:
                logger_.debug("Found a replacement from globals")
                newVal = global_expr_g_.node[v]['reduced']
                val = val.replace(v, newVal)
            else:
                pass
    msg += ', NEW = %s' % val
    logger_.info(msg)
    return val


def compute_volume( network ):
    """Compute the volume of compartment """
    global globals_
    if 'geometry' in globals_:
        if globals_['geometry'] == 'cylinder':
            r = eval(globals_['radius'])
            l = eval(globals_['length'])
            globals_['volume'] = str( pi * r * r * l )
        else:
            msg = 'For geometry %s, you must assign a volume' % globals_['geometry']
            assert globals_.get('volume',False), msg
    logger_.info('Volume of compartment : %s' % globals_['volume'])

def deduce_missing_paramters( network ):
    """deduce_missing_paramters Some parameters requires other paramters to be
    set. Enable them.

    :param network:
    """
    global globals_
    if 'diffusion_length' in globals_:
        logger_.info("Diffusion length found. Enabling diffusion in this compartment")
        globals_['enable_diffusion'] = True
    else:
        globals_['enable_diffusion'] = False
        logger_.info("This compartment does not support diffusion")
                
def pre_process( network ):
    """ Pre-process the graph in a way that all subtitutions are made.
    In all key = val, val should be string type.
    """
    global global_expr_g_
    global globals_
    globals_ = network.graph['graph']
    compute_volume( network )
    deduce_missing_paramters( network )
    build_global_expression_graph( network )
    flatten_global_expressions( network )

    # Now global expressions are reduced, we can process each node expresions.
    # Note that expression on node are local to nodes only, except that they are
    # refer to global variables.
    for n in network.nodes():
        reduce_node_expr(n, network)
