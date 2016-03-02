"""parser.py: 

It uses local pydot module and then convert it to networkx graph.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


import networkx as nx
import networkx.drawing.nx_agraph as nxpy

def to_networkx( dot_file ):
    """read dot_file and turn it into a networkx graph. 
    """
    nxG = nxpy.read_dot( dot_file )
    return nxG
