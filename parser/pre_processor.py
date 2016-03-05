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
import re

def pre_process( graph ):
    for n in graph.nodes():
        print n
    return graph
