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
keys_with_expressions_ = [ 'kf', 'kb', 'numKf', 'numKb', 'N', 'conc' ]
global_expr_g_ = nx.DiGraph( )

def get_identifiers( syntax_tree ):
    idents = set()
    for n in ast.walk( syntax_tree ):
        if isinstance( n, ast.Name ):
            idents.add(n.id)
        else:
            pass
    return idents

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
        try:
            st = ast.parse( v )
        except SyntaxError as e:
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
    logger_.debug("Global variables: %s" % global_expr_g_.nodes())
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
    variables as well as global variables in the expression. DO NOT touch
    variable 't'. Currently only a simple reduction mechanism is supported. We
    do not build a dependency graph for expression. Therefore each
    sub-expression should be reducible indepedably.

    :param n: The node of network currently being processed.
    :param network: Whole network.
    """

    global keys_with_expressions_ 
    global global_expr_g_
    attr = network.node[n]
    for k, v in attr.items():
        attr[k] = reduce_expr( v )[0]
    for k, v in attr.items():
        reduce_key_val_on_node( k, v, attr, network )

def reduce_key_val_on_node( key, val, local_vars, network):
    """reduce_key_val_on_node Reduce the key=value to key=new_val where new_val
    is reduced val after replacing local (form local_vars) and global variables.

    :param key:
    :param val:
    :param node:
    :param network:
    """

    global global_expr_g_
    if key not in keys_with_expressions_:
        return False

    st = None
    try:
        st = ast.parse( val )
    except SyntaxError as e:
        logger_.warn("Expr %s=%s (node %s) is malformed" % (key, val, node))
        logger_.warn("... Ignoring. ")
        return False

    assert st, "If we are here we must have parsed the expression to ast"
    msg = '|KEY %s| OLD expr = %s' % (key, val)
    if not reduce_expr( val )[1]:
        # It can't be reduced. Don't change it.
        otherVars = get_identifiers( st )
        print otherVars
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
    logger_.debug(msg)
                
def pre_process( network ):
    """ Pre-process the graph in a way that all subtitutions are made.
    In all key = val, val should be string type.
    """
    global global_expr_g_
    build_global_expression_graph( network )
    flatten_global_expressions( network )

    # Now global expressions are reduced, we can process each node expresions.
    # Note that expression on node are local to nodes only, except that they are
    # refer to global variables.
    for n in network.nodes():
        reduce_node_expr(n, network)
