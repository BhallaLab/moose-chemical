"""ply_yacc.py: 

    Yacc module for python.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"



import ply.yacc as yacc

# Get the token map from the lexer.  This is required.
from ply_lexer import tokens

def p_compartment(p):
    'compartment : COMPARTMENT ID '

# Build the parser
chemical_parser = yacc.yacc()
