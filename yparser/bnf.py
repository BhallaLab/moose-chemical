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

from .pyparsing import *
import xml
import xml.etree.ElementTree as etree
import utils.typeclass as tc

# Function to generate graph.
xml_ = etree.Element( 'yacml' )
globals_ = etree.SubElement( xml_, 'list_of_parameters' )
recipes_ = etree.SubElement( xml_, 'list_of_recipes' )
compartments_ = etree.SubElement( xml_, 'list_of_compartments' )
species_ = etree.SubElement(xml_, 'list_of_species' )
model_ = etree.SubElement( xml_, 'model' )

def add_variable( tokens, **kwargs):
    var = etree.Element( 'variable' )
    constExpr, keyValList = tokens
    var.attrib['type'] = constExpr
    key = etree.SubElement( var, 'name' )
    val = etree.SubElement( var, 'value' )
    key.text = keyValList[0]
    val.text = keyValList[1]
    return var

def add_species( tokens, **kwargs ):
    sp = etree.Element( 'species' )
    sp.text = tokens[2]
    attribs = tokens[3]
    for k, v in attribs:
        sp.attrib[ k ] = str(v)
    sp.attrib['is_buffered'] = tokens[0]
    return sp

def add_recipe( tokens, **kwargs):
    recipe = etree.Element( 'recipe' )
    nameElem = etree.SubElement( recipe, 'name' )
    nameElem.text = tokens[1]
    # Now time to add other xml elements into recipe tree.
    for x in tokens:
        if isinstance(x, etree.Element ):
            recipe.append( x )
    return recipe

def add_reaction_declaration( tokens, **kwargs ):
    reacId = etree.Element( 'reaction_declaration' )
    for x in tokens[2]:
        key, val = x
        reacId.attrib[key] = val
    return reacId

def add_reaction_instantiation( tokens, **kwargs ):
    reac = etree.Element( 'reaction' )
    subsList, r, prdList = tokens
    for sub in subsList:
        sub = etree.SubElement( reac, 'substrate' )
    for prd in prdList:
        prd = etree.SubElement( reac, 'product' )
    
    # A simple identifier means reaction is declared elsewhere, a list means
    # that key, value pairs are declared.
    if type( r ) != str:
        for k, v in r:
            reac.attrib[k] = v
    else:
        reac.attrib['id'] = r
    return reac

##
# @brief Add a compartment to XML AST.
#
# @param tokens
# @param kwargs
#
# @return 
def add_compartment( tokens, **kwargs ):
    compt = etree.Element( 'compartment' )
    return compt


# YACML BNF.
pIdentifier = pyparsing_common.identifier
COMPT_BEGIN = Keyword("compartment")
RECIPE_BEGIN = Keyword( "recipe" )
HAS = Keyword("has").suppress()
IS = Keyword( "is" ).suppress()
END = Keyword("end") + Optional( pIdentifier )
SPECIES = Keyword( "species" ) | Keyword( "pool" ) | Keyword( "enzyme" )
REACTION = Keyword( "reaction" ) | Keyword( "reac" ) | Keyword( "enz_reac" )
GEOMETRY = Keyword("cylinder") | Keyword( "cube" ) | Keyword( "Spine" )
VAR = Keyword( "var" ) 
CONST = Keyword( "const" ) 
BUFFERED = Keyword( "buffered" ).setParseAction( lambda x: 'true' )

pComptName = pIdentifier
pSpeciesName = pIdentifier
pEOS = Literal( ";" ).suppress()
LBRAC = Literal("[").suppress()
RBRAC = Literal("]").suppress()
LCBRAC = Literal("{").suppress()
RCBRAC = Literal("}").suppress()
EQUAL = Literal('=').suppress()
RREAC = Literal( "->" ).suppress()
LREAC = Literal( "<-" ).suppress()

pNumVal = pyparsing_common.numeric \
        | pyparsing_common.integer \
        | pyparsing_common.number | Regex( r'\.\d+' )
pNumVal.setParseAction( lambda x: str(x[0]) )

# Parser for key = value expression.
pValue = ( pNumVal | pIdentifier | quotedString() )

pKeyVals = Group( pIdentifier + EQUAL + pValue )

pKeyValList = LBRAC + Group( delimitedList( pKeyVals )) + RBRAC
pSpeciesExpr = Optional(BUFFERED, 'false') + SPECIES + pSpeciesName +  pKeyValList + pEOS
pSpeciesExpr.setParseAction( add_species )

# Species name with stoichiometry coefficient e.g 2a + 3b 
pStoichNumber = Optional(Word(nums), '1') 
pSpeciesNameWithStoichCoeff = Group( pStoichNumber + pSpeciesName )

# Expression for reactions.
pSubstrasteList = Group( delimitedList( pSpeciesNameWithStoichCoeff, '+' ) )
pProductList = Group( delimitedList( pSpeciesNameWithStoichCoeff, '+' ) )

# Reactions. Parses expressions like the following.
#
#       a + b <- kf = 10, kb = 1e-2 -> 2c + 9d,
# Or,
#       reaction rA [ kf = 10, kb = 1e-2 ]
#       a + b <- rA -> 2c + 9d 
#
# Both of the above expressions are equivalent and should have same AST tree in
# final model.
pReacName = pIdentifier
pReacDecl = REACTION + pReacName + pKeyValList + pEOS
pReac = pReacName | pKeyValList 
pReacInst = pSubstrasteList + LREAC + pReac + RREAC + pProductList + pEOS

pReacDecl.setParseAction( add_reaction_declaration )
pReacInst.setParseAction( add_reaction_instantiation )

pReacExpr = pReacDecl | pReacInst

pTypeExpr = CONST | VAR
pVariableExpr = ( Optional(pTypeExpr, 'var') + pKeyVals) + pEOS
pVariableExpr.setParseAction( add_variable )

# Name of the recipe
pRecipeName = pIdentifier

# Recipe instantiation expression
pRecipeType = pIdentifier 
pInstExpr = pRecipeType + pRecipeName + END

# Valid YAXML expression
pYACMLExpr = pSpeciesExpr | pReacExpr | pVariableExpr | pInstExpr
pGeometry = GEOMETRY + Optional( pKeyValList )

# Compartment 
pCompartmentBody = OneOrMore( pYACMLExpr )
pCompartment = COMPT_BEGIN + pComptName + IS + pGeometry + HAS + pCompartmentBody + END
pCompartment.setParseAction( add_compartment )

# Recipe 
pRecipeBody = OneOrMore( pYACMLExpr )
pRecipe =  RECIPE_BEGIN + pRecipeName + IS  + pRecipeBody + END 
pRecipe.setParseAction( add_recipe )

yacmlBNF_ = OneOrMore( pRecipe | pCompartment  ) 
yacmlBNF_.ignore( javaStyleComment )
