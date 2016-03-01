"""warnings.py: 

Keep developement related warnings.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


def issue_72( ):
    msg = 'SORRY ======================================================='
    msg += '\nUnfortunately, reading conc (float) is not supported in function.'
    msg += '\nYou need to write an expression for N.'
    msg += '\nThis is to avoid volume scaling effects during simulation.'
    msg += '\nIn priciple, "conc = expr" can be supported.  ' 
    msg += '\nSee request #72 on https://github.com/BhallaLab/moose-core'
    msg += '\n==========================================================='
    return msg
