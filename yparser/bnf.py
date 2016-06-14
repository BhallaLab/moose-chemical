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
import lxml.etree as etree
import lxml
import utils.typeclass as tc
import utils.helper as helper
from collections import defaultdict

# Function to generate graph.
xml_ = etree.Element( 'yacml' )

globals_ = {}

reac_params_ = [ 'kf', 'kb', 'numkf', 'numkb', 'km' ]

def attach_val_with_reduction( elem, val ):
    elem.text, elem.attrib['is_reduced'] = helper.reduce_expr( val )

def add_variable( tokens, **kwargs):
    var = etree.Element( 'variable' )
    constExpr, (key, val) = tokens
    var.attrib['type'] = constExpr
    var.attrib['name'] = key
    attach_val_with_reduction( var, val )
    return var

def add_species( tokens, **kwargs ):
    sp = etree.Element( 'species' )
    sp.attrib['name'] = tokens[2]
    attribs = tokens[3]
    for k, v in attribs:
        if k.lower() in [ 'n', 'conc' ]:
            paramXml = etree.SubElement( sp, 'parameter' )
            paramXml.attrib['name'] = k
            attach_val_with_reduction( paramXml, v )
        else:
            varXml  = etree.SubElement( sp, 'variable' )
            varXml.attrib['name'] = k
            attach_val_with_reduction( varXml, v )
            
    sp.attrib['is_buffered'] = tokens[0]
    return sp

def add_recipe( tokens, **kwargs):
    recipe = etree.Element( 'recipe' )
    recipe.attrib['id'] = tokens[1]
    # Now time to add other xml elements into recipe tree.
    for x in tokens:
        if isinstance(x, etree._Element ):
            recipe.append( x )
    xml_.append( recipe )
    return recipe

def add_reaction_declaration( tokens, **kwargs ):
    reacId = etree.Element( 'reaction_declaration' )
    reacId.attrib['id'] = tokens[1]
    for key, val in tokens[2]:
        if key.lower() in reac_params_:
            elem = etree.SubElement( reacId, 'parameter' )
            elem.attrib['name'] = key
            attach_val_with_reduction( elem, val )
        else:
            elem = etree.SubElement( reacId, 'variable' )
            elem.attrib['name'] = key
            attach_val_with_reduction( elem, val )
    return reacId

def add_reaction_instantiation( tokens, **kwargs ):
    reac = etree.Element( 'reaction' )
    subsList, r, prdList = tokens
    nameOfReac = ''
    for sub in subsList:
        subXml = etree.SubElement( reac, 'substrate' )
        subXml.attrib['stoichiometric_number'] = sub[0]
        subXml.text = sub[1]
        nameOfReac += sub[1]
    nameOfReac += '__TO__'
    for prd in prdList:
        prdXml = etree.SubElement( reac, 'product' )
        prdXml.attrib['stoichiometric_number'] = prd[0]
        prdXml.text = prd[1]
        nameOfReac += prd[1]
    
    # A simple identifier means reaction is declared elsewhere, a list means
    # that key, value pairs are declared.
    if type( r ) != str:
        for k, v in r:
            if k.lower( ) in reac_params_:
                elem = etree.SubElement( reac, 'parameter' )
            else:
                elem = etree.SubElement( reac, 'variable' )
            elem.attrib[ 'name' ] = k
            attach_val_with_reduction( elem, v )
    else:
        reac.attrib['instance_of'] = r

    reac.attrib['name'] = nameOfReac
    return reac

def add_recipe_instance( tokens, **kwargs ):
    print( '[INFO] Adding an instance of reaction.' )
    recipeInst = etree.Element( 'recipe_instance' )
    recipeInst.attrib['instance_of'] = tokens[0]
    recipeInst.text = tokens[1]
    return recipeInst

def add_model( tokens, **kwargs ):
    global xml_
    print( '[INFO] Adding top-level model ' )
    modelXml = etree.Element( 'model' )
    modelXml.attrib[ 'name' ] = tokens[1]
    for t in tokens[2:]:
        if isinstance(t, etree._Element ):
            modelXml.append( t )
    xml_.append( modelXml )

def add_compt_instance( tokens, **kwargs ):
    instXml = etree.Element( 'compartment_instance' )
    instXml.text = tokens[1]
    instXml.attrib['instance_of'] = tokens[0]
    
    # attach all other tokesn.
    for x in tokens[2:]:
        if isinstance( x, lxml._Element ):
            instXml.append( x )
        else:
            instXml.attrib[x[0]] = x[1]
    return instXml

def add_simulator( tokens, **kwargs ):
    simXml = etree.Element( 'simulator' )
    simXml.text = tokens[1]
    for k, v in tokens[2]:
        simXml.attrib[k] = v
    return simXml

##
# @brief Add a compartment to XML AST.
#
# @param tokens
# @param kwargs
#
# @return 
def add_compartment( tokens, **kwargs ):
    global xml_
    print( '[INFO] Adding compartment %s' % tokens )
    compt = etree.Element( 'compartment' )
    compt.attrib['id'] = tokens[1]

    comptGeom = etree.SubElement( compt, 'geometry' )
    comptGeom.attrib['shape'] = tokens[2]

    for k, v in tokens[3]:
        elem = etree.SubElement( comptGeom, 'variable' )
        elem.attrib['name'] = k
        attach_val_with_reduction( elem, v )

    # And append rest of the xml/
    for x in tokens[4:]:
        if isinstance( x, etree._Element ):
            compt.append( x )
    xml_.append( compt )
    return compt

##
# @brief Main parser function 
#
# @param tokens. List of tokens.
# @param kwargs. Dictionary of arguments.
#
# @return Return the AST in XML.
def parser_main( tokens, **kwargs ):
    global xml_
    print tokens
    return xml_


# YACML BNF.
COMPT_BEGIN = Keyword("compartment")
RECIPE_BEGIN = Keyword( "recipe" )
MODEL_BEGIN = Keyword( "model" ) | Keyword( "pathway" )
HAS = Keyword("has").suppress()
IS = Keyword( "is" ).suppress()
SPECIES = Keyword( "species" ) | Keyword( "pool" ) | Keyword( "enzyme" )
REACTION = Keyword( "reaction" ) | Keyword( "reac" ) | Keyword( "enz_reac" )
GEOMETRY = Keyword("cylinder") | Keyword( "cube" ) | Keyword( "spine" )
VAR = Keyword( "var" ) 
CONST = Keyword( "const" ) 
BUFFERED = Keyword( "buffered" ).setParseAction( lambda x: 'true' )
END = Keyword("end").suppress()
SIMULATOR = Keyword( "simulator" )

anyKeyword = COMPT_BEGIN | RECIPE_BEGIN | MODEL_BEGIN \
        | HAS | IS | SPECIES | REACTION \
        | GEOMETRY | VAR | CONST | BUFFERED | END \
        | SIMULATOR

# literals.
pEOS = Literal( ";" ).suppress()
LBRAC = Literal("[").suppress()
RBRAC = Literal("]").suppress()
LCBRAC = Literal("{").suppress()
RCBRAC = Literal("}").suppress()
EQUAL = Literal('=').suppress()
RREAC = Literal( "->" ).suppress()
LREAC = Literal( "<-" ).suppress()

anyLiteral = pEOS | LBRAC | RREAC | LCBRAC | RCBRAC | EQUAL | RREAC | LREAC

pIdentifier = pyparsing_common.identifier
# Make sure no keyword is matched as identifier.
pIdentifier.ignore( anyKeyword )


pComptName = pIdentifier
pSpeciesName = pIdentifier
pNumVal = pyparsing_common.numeric \
        | pyparsing_common.integer \
        | pyparsing_common.number | Regex( r'\.\d+' )
pNumVal.setParseAction( lambda x: str(x[0]) )

# Parser for key = value expression.
pValue = pNumVal | pIdentifier | quotedString 
quotedString.setParseAction( lambda x: (''.join(x)).replace('"', '') )

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
pRecipeInstExpr = pRecipeType + pRecipeName + pEOS
pRecipeInstExpr.setParseAction( add_recipe_instance )

# Geometry of compartment.
pGeometry = GEOMETRY + Optional( pKeyValList, [] )

# Valid YAXML expression
pYACMLExpr = pSpeciesExpr | pReacExpr | pVariableExpr | pRecipeInstExpr

##
# @brief Compartment can have reactions, species, or instance of other recipe.
# Compartment also have solver, geometry and diffusion.
pCompartmentBody = OneOrMore( pYACMLExpr )
pCompartment = COMPT_BEGIN + pComptName + IS + pGeometry + HAS + pCompartmentBody + END
pCompartment.setParseAction( add_compartment )

# Recipe 
pRecipeBody = OneOrMore( pYACMLExpr )
pRecipe =  RECIPE_BEGIN + pRecipeName + IS  + pRecipeBody + END 
pRecipe.setParseAction( add_recipe )

# Model
# A model can have list of compartments instances. Solver, runtime and other
# information. It can also have plot list but it should not be a part of YACML.

pSimulatorName = pIdentifier
pSimulator = SIMULATOR + pSimulatorName + Optional( pKeyValList ) + pEOS
pSimulator.setParseAction( add_simulator )

pComptType = pIdentifier 
pComptInstName = pIdentifier 
pComptInst = pComptType + pComptInstName + pEOS
pComptInst.setParseAction( add_compt_instance )

pModelName = pIdentifier
pModelStmt = ( pComptInst | pSimulator )

pModel = MODEL_BEGIN + pModelName + HAS +  OneOrMore( pModelStmt ) + END
pModel.setParseAction( add_model )

# There must be one and only one model statement in each file. Each model must
# have at least one compartment. Each compartment must have at least one recipe.
yacmlBNF_ = OneOrMore( pRecipe | pCompartment ) + pModel

# yacmlBNF_ = OneOrMore( pCompartment )
yacmlBNF_.setParseAction( parser_main )
yacmlBNF_.ignore( javaStyleComment )
#yacmlBNF_.setDebug( )
