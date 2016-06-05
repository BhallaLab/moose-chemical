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

from yparser.yacml_bnf import *

def main( ):
    print( '[INFO] Main function' )
    print('Testing ' )
    print(pKeyVals.parseString( 'AV = 6.023e23' ))
    print(pCompartment.parseString( 
        '''
        compartment PSD is 
            cube 
        has
            AV = 6.023e23;
        end PSD
        '''
        ))
    print( pNumVal.parseString( "1.5111" ) )
    print( pNumVal.parseString( ".5111" ) )
    print( pNumVal.parseString( "-1.35e13" ) )
    print( pNumVal.parseString( "1e-2" ) )
    print( pReacExpr.parseString( '2a + 3b <- r0 -> c + 9d;' ) )
    print( pYACMLExpr.parseString( 'const vm = "2.9*x";' ) )

if __name__ == '__main__':
    main()
