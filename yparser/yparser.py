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


import yparser.bnf  as bnf
from config import logger_
import lxml.etree as etree

def parse_text( text ):
    pass

def parse( filename ):
    print( '[INFO] Parsing %s' % filename )
    data = bnf.yacmlBNF_.parseFile( filename )
    return data[0]
