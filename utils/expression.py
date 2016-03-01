"""expression.py: 

    Function on expression.
"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import re
from .. import py_expression_eval as  pee

parser = pee.Parser()

def get_ids(expr):
    ids = re.findall(r'(?P<id>[_a-zA-Z]\w*)', expr)
    return ids


def replace_possible_subexpr(expr, constants, ids):
    """ If a id value can be converted to float, its a constant. Else its a
    subexpression
    """
    for i in ids:
        if i in constants:
            try: 
                v = float(constants[i])
            except:
                # NOTE: sometimes a constant may be quoted. We don't want to
                # have one more quotation inside quote.
                replaceWith = constants[i].replace('"', '')
                expr = expr.replace(i, replaceWith)
    return expr

