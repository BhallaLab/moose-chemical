"""test_bnf_parser.py: 

    Test the BNFC implementation.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import sys
import os

d = os.path.dirname( os.path.abspath( __file__ ) )
sys.path.append( os.path.join(d, '../yparser' ) )

# from ..yparser.yacml_bnf import *
from yacml_bnf import *

def main( ):
    print( '[INFO] Main function' )

    print('Testing ' )
    print pKeyVals.parseString( 'AV = 6.023e23' )
    print pCompartment.parseString( 
        '''compartment PSD has
            AV = 6.023e23;
        end PSD
        '''
        )
    print pNumVal.parseString( "1.5111" )
    print pNumVal.parseString( ".5111" )
    print pNumVal.parseString( "-1.35e13" )
    print pNumVal.parseString( "1e-2" )
    print pReacExpr.parseString( '2a + 3b <- r0 -> c + 9d;' )

if __name__ == '__main__':
    main()
