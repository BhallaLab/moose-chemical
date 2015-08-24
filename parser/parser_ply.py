"""parser_ply.py: 

    Parser written in PLY.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

from ply_lexer import lexer
from ply_yacc import chemical_parser

def parse(filename):
    with open(filename, "r") as f:
        text = f.read()
        return chemical_parser.parse(text)

if __name__ == '__main__':
    print parser('../_models/simple_reaction.dot')

