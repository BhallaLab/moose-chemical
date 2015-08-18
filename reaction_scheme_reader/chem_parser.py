"""parser.py: 

    Parser a given chemical file and create moose network.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


import sys
import ply
from chem_lexer import tokens
import moose


import ply.yacc as yacc
        
def p_error(p):
    raise TypeError("unknown text at %r" % (p.value,))

def p_reaction(p):
    """
    reaction : reactants LEFT_REAC params RIGHT_REAC  products
    """
    pass

def p_params(p):
    """
    params : param 
           | params COMMA param
    """

def p_reactants(p):
    """
    reactants : species 
              | reactants PLUS species
    """
    pass

def p_products(p):
    """
    products : species
             | products PLUS species
    """

def p_param(p):
    """
    param : NAME EQUALS DECIMAL
    """
    pass

def p_species(p):
    """
    species : NAME LPAREN params RPAREN
    """
    print "Single species"

parser = yacc.yacc()
