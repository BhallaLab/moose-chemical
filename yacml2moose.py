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


import networkx.drawing.nx_agraph as nxAG
import moose
import moose.print_utils as pu
import moose.utils as mu
import re
from utils import test_expr as te
from utils import expression as _expr
import notify as warn
import config
from utils import typeclass as tc
import lxml.etree as etree
# from utils.helper import *
logger_ = config.logger_


def do_local_constant_propagation( elem ):
    # step 1, get all the local variables
    print( '[DEBUG] Replacing in %s' % elem.tag )
    reduced = elem.xpath( '//variable[@is_reduced="true"]' )
    unreduced = elem.xpath( '//variable[@is_reduced="false"]' )


def do_constant_propagation( tree ):
    # get all instance of variables
    variables = tree.xpath( '//variable' )
    elems = set()
    for var in variables:
        elems.add( var.getparent( ) )
    [ do_local_constant_propagation( e ) for e in elems ]

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
    return xml
