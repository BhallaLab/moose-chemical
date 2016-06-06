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
import networkx.drawing.nx_agraph as nxAG
import tempfile
import re
import bnf 
from config import logger_
import pylab

def parse_text( text ):
    pass

def parse( filename ):
    print( '[INFO] Parsing %s' % filename )
    # bnf.yacmlBNF_.setDebug( )
    data = bnf.yacmlBNF_.parseFile( filename )
    nx.draw( bnf.network_ )
    pylab.show( )

def remove_comments( text ):
    text = re.sub( r'\/\*.+?\*\/', '', text, flags = re.DOTALL )
    text = re.sub( r'\s+\/\/.*', '', text )
    return text

def yacml_to_dot( yacml_text ):
    """Convert yacml_text to valid graphviz text """
    yacml_text = remove_comments( yacml_text )
    comptPat = re.compile(
            r'compartment\s+(?P<name>\w+)\s+?{(?P<body>.+?)}'
            , re.DOTALL
            )
    for compt in comptPat.findall( yacml_text ):
        compartments_[compt[0]] = compt[1]

    gvText = yacml_text.replace( 'compartment', 'digraph' )
    return gvText

def create_graph( yacml_file, **kwargs ):
    parse( yacml_file )
    quit( )
    logger_.info("Parsing %s to create netowrkx graph" % yacml_file)
    # Create a temporary file to convert the yacml file to dot file. After this,
    # parser the dot file to generate the graph.
    with tempfile.NamedTemporaryFile( delete = True , suffix = '.dot') as dotFile:
        with open( yacml_file, "r") as f:
            modelText = f.read()
        logger_.info("Generating graphviz : %s" % dotFile.name)
        dotFile.write(yacml_to_dot(modelText))
        dotFile.flush()
        try:
            network = nxAG.read_dot(dotFile.name)
        except Exception as e:
            logger_.fatal( 'Failed to load input file. Error was %s' % e )
            quit()

    network = nx.MultiDiGraph( network )
    network.graph['graph']['filename'] = yacml_file
    assert network.number_of_nodes() > 0, "Zero molecules"
    return network
