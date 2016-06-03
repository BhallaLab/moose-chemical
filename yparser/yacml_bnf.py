"""yacml_bnf.py: 

    BNFC grammar of YACML.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

from pyparsing import *

# YACML BNF.
yacmlBNF_ = None
pIdentifier = Word( alphas+"_", alphanums+"_" )
pComptBegin = Keyword("compartment")
pHas = Keyword("has")
pEnd = Keyword("end") + Optional( pIdentifier )

pComptName = pIdentifier
pPoolName = pIdentifier
pEOS = Literal( ";" ) 
LBRAC = Literal("[")
RBRAC = Literal("]")
LCBRAC = Literal("{")
RCBRAC = Literal("}")
EQUAL = Literal('=')
RREAC = Literal( "->" )
LREAC = Literal( "<-" )

pReal = pyparsing_common.sciReal | pyparsing_common.real
pReal.setParseAction( lambda t: float(t[0]) )
pDecimal = Regex(r'[+-]?[0-9]\d*(.\d+)?') | Regex( r'[+-]?[0-9]*\.\d+' )
pNumVal = ( pReal  | pDecimal )
pNumVal.setParseAction( lambda t: float(t[0]) )

# Parser for key = value expression.
pValue = ( pNumVal | pIdentifier | quotedString() )

pKeyVals = pIdentifier + EQUAL + pValue 

pPoolExpr = pPoolName + LBRAC + delimitedList( pKeyVals ) + RBRAC + pEOS

# Pool name with stoichiometry coefficient e.g 2a + 3b 
pStoichNumber = Optional(Word(nums), '1') 
pStoichNumber.setParseAction( lambda x: int(x[0] ) )
pPoolNameWithStoichCoeff = Group( pStoichNumber + pPoolName )

# Expression for reactions.
pSubstrasteList = Group( delimitedList( pPoolNameWithStoichCoeff, '+' ) )
pProductList = Group( delimitedList( pPoolNameWithStoichCoeff, '+' ) )
pReacExpr = pIdentifier
pReacExpr = pSubstrasteList + LREAC + pReacExpr + RREAC + pProductList + pEOS

pVariableExpr = pKeyVals + pEOS

# Valid YAXML expression
pYACMLExpr = pPoolExpr | pReacExpr | pVariableExpr 

pCompartmentBody = OneOrMore( pYACMLExpr )
pCompartment = pComptBegin + pComptName + pHas + pCompartmentBody + pEnd

yacmlBNF_ = OneOrMore( pCompartment) 
yacmlBNF_.ignore( javaStyleComment )

def main( ):
    print('Testing ' )
    print pKeyVals.parseString( 'AV = 6.023e23' )
    print pCompartment.parseString( 
        '''compartment PSD has
            AV =  6.023e23 
        end compartment
        '''
        )
    print pNumVal.parseString( "1.5111" )
    print pNumVal.parseString( ".5111" )
    print pNumVal.parseString( "-1.35e13" )
    print pNumVal.parseString( "1e-2" )
    print pReacExpr.parseString( '2a + 3b <- r0 -> c + 9d' )

if __name__ == '__main__':
    main()
