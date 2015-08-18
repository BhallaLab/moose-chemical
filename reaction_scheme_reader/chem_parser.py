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


import ply.yacc as yacc
        
def p_error(p):
    raise TypeError("unknown text at %r" % (p.value,))

def p_chemical_equation(p):
    """
    chemical_equation : 
    chemical_equation : species_list 
    """
    pass

def p_species_list(p):
    """
    species_list : species_list species
    """
    pass

def p_species(p):
    "species_list : species"
    pass

def p_single_species(p):
    """
    species : NAME
    species : NAME NUMBER 
    """
    pass

parser = yacc.yacc()
