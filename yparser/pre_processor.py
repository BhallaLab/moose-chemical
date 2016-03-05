"""pre_processor.py: 

Given a graph, replace its expressions on nodes.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
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
eys_with_expressions_ = [ 'kf', 'kb', 'numKf', 'numKb', 'N', 'conc' ]
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
    print attrs


def reduce_expr( expr ):
    try:
        newExpr = str( eval( expr ) )
        return newExpr, True
    except NameError as e:
        return expr, False
    except Exception as e:
        logger_.warn("Unknown error in expr: %s" % expr)
    return expr, False


def build_global_expression_graph( network ):
    """Dependency graph. Which variable depends on which one 
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

def flatten_expression_graph( g ):
    # [ pre_process_node(x, graph) for x in graph.nodes() ]
    for x in nx.dfs_postorder_nodes( g ):
        if 'expr' not in g.node[x]:
            continue
        expr = g.node[x]['expr']
        logger_.info("Old expression on %s is %s" % (x, expr))
        if g.node[x].get('reduced', ''):
            logger_.debug("%s is already reduced" % x)
        else:
            for xx in g.successors(x):
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
        if reduce_expr( g.node[x]['expr'] )[1]:
            g.node[x]['reduced'] = reduce_expr( g.node[x].get('expr') )[0]
            g.node[x]['expr'] = g.node[x]['reduced']
        logger_.info("New expression on %s is: %s" % (x, g.node[x].get('expr')))

def pre_process( network ):
    """ Pre-process the graph in a way that all subtitutions are made.
    In all key = val, val should be string type.
    """
    global global_expr_g_
    build_global_expression_graph( network )
    flatten_expression_graph( global_expr_g_ )
    nx.draw( global_expr_g_ , with_labels = True )
    import pylab
    pylab.show()
    quit()
    return graph
