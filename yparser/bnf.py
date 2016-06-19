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

import lxml
import math

import lxml.etree as etree
import utils.helper as helper
import utils.xml as xml

from collections import defaultdict
from copy import deepcopy
from config import logger_
from .pyparsing import *

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
    logger_.info( 'Adding model ' )
    modelXml = etree.Element( 'model' )
    modelXml.attrib[ 'name' ] = tokens[1]
    for t in tokens[2:]:
        if isinstance(t, etree._Element ):
            modelXml.append( t )
    xml_.append( modelXml )

def add_compartment_instance( tokens, **kwargs ):
    instXml = etree.Element( 'compartment_instance' )
    instXml.attrib['type'] = tokens[0]
    instXml.text = tokens[1]
    instXml.attrib['instance_of'] = tokens[2]
    # attach all other tokesn.
    for x in tokens[3]:
        if isinstance( x, etree._Element ):
            instXml.append( deepcop( x ) )
        else:
            instXml.attrib[x[0]] = x[1]
    return instXml

def add_simulator( tokens, **kwargs ):
    simXml = etree.Element( 'simulator' )
    simXml.text = tokens[1]
    for k, v in tokens[2]:
        simXml.attrib[k] = v
    return simXml

def compute_volume( geom_xml ):
    shape = geom_xml.attrib[ 'shape' ]
    vol = 0.0
    if shape == "cylinder":
        l, r = [ 
                xml.get_value_from_parameter_xml( geom_xml, x ) for x in 
                [ "length", "radius" ] 
                ]
        vol = math.pi * r * r * l 
    elif shape == 'cube' :
        l, w, h = [ xml.get_value_from_parameter_xml( geom_xml, x ) for x in
                [ "length", "width", "height" ] 
                ]
        vol = l * w * h
    else:
        logger_.warn( 'Failed to compute volume for shape %s' % shape )
    return vol


def add_geometry( tokens, **kwargs ):
    geom = etree.Element( 'geometry' )
    geom.attrib['diffusion'] = tokens[0]
    geom.attrib['shape'] = tokens[1]
    for k, v in tokens[2]:
        elem = etree.SubElement( geom, 'parameter' ) 
        elem.attrib['name'] = k
        attach_val_with_reduction( elem, v )
    vol = compute_volume( geom )
    volParam = etree.SubElement( geom, 'parameter' )
    volParam.attrib[ 'name' ] = 'volume'
    volParam.text = str( vol )
    return geom

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
    compt.append( deepcopy( tokens[2] ) ) 
    # And append rest of the xml/
    for x in tokens[3:]:
        if isinstance( x, etree._Element ):
            compt.append( deepcopy( x ) )
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
COMPARTMENT = Keyword("compartment")
RECIPE_BEGIN = Keyword( "recipe" )
MODEL = Keyword( "model" ) | Keyword( "pathway" )
HAS = Keyword("has").suppress()
IS = Keyword( "is" ).suppress()
SPECIES = Keyword( "species" ) | Keyword( "pool" ) | Keyword( "enzyme" )
REACTION = Keyword( "reaction" ) | Keyword( "reac" ) | Keyword( "enz_reac" )
GEOMETRY = Keyword("cylinder") | Keyword( "cube" ) | Keyword( "spine" )
VAR = Keyword( "variable" ) 
CONST = Keyword( "const" ) 
BUFFERED = Keyword( "buffered" ).setParseAction( lambda x: 'true' )
END = Keyword("end").suppress()
SIMULATOR = Keyword( "simulator" )
STOCHASTIC = Keyword( "stochastic" )
DETEMINISTIC = Keyword( "deterministic" ) | Keyword( "well-mixed" )
DIFFUSIVE = Keyword( "diffusive" )

anyKeyword = COMPARTMENT | RECIPE_BEGIN | MODEL \
        | HAS | IS | SPECIES | REACTION \
        | GEOMETRY | VAR | CONST | BUFFERED | END \
        | DETEMINISTIC | DETEMINISTIC \
        | DIFFUSIVE | SIMULATOR 

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
pVariableExpr = ( Optional(pTypeExpr, 'variable') + pKeyVals) + pEOS
pVariableExpr.setParseAction( add_variable )

# Name of the recipe
pRecipeName = pIdentifier

# Recipe instantiation expression
pRecipeType = pIdentifier 
pRecipeInstExpr = pRecipeType + pRecipeName + pEOS
pRecipeInstExpr.setParseAction( add_recipe_instance )

# Geometry of compartment.
pDiffusive = DIFFUSIVE
pGeometry = Optional(pDiffusive, "non-diffusive" ) + GEOMETRY \
        + Optional( pKeyValList, [] )
pGeometry.setParseAction( add_geometry )

# Valid YAXML expression
pYACMLExpr = pSpeciesExpr | pReacExpr | pVariableExpr | pRecipeInstExpr

##
# @brief Compartment can have reactions, species, or instance of other recipe.
# Compartment also have solver, geometry and diffusion.
pCompartmentBody = OneOrMore( pYACMLExpr )
pCompartment = COMPARTMENT + pComptName + IS + pGeometry +  HAS + pCompartmentBody + END
pCompartment.setParseAction( add_compartment )

# Recipe 
pRecipeBody = OneOrMore( pYACMLExpr )
pRecipe =  RECIPE_BEGIN + pRecipeName + HAS  + pRecipeBody + END 
pRecipe.setParseAction( add_recipe )

# Model
# A model can have list of compartments instances. Solver, runtime and other
# information. It can also have plot list but it should not be a part of YACML.

pSimulatorName = pIdentifier
pSimulator = SIMULATOR + pSimulatorName + Optional( pKeyValList ) + pEOS
pSimulator.setParseAction( add_simulator )

pComptType = pIdentifier 
pComptInstName = pIdentifier 
pComptNature = STOCHASTIC | DETEMINISTIC
pComptInst =  Optional( pComptNature, "deterministic" ) \
        + pComptInstName + IS + pComptType \
        + Optional( pKeyValList, [] ) + pEOS

pComptInst.setParseAction( add_compartment_instance )

pModelName = pIdentifier
pModelStmt = ( pComptInst | pSimulator )

pModel = MODEL + pModelName + HAS +  OneOrMore( pModelStmt ) + END
pModel.setParseAction( add_model )

# There must be one and only one model statement in each file. Each model must
# have at least one compartment. Each compartment must have at least one recipe.
yacmlBNF_ = OneOrMore( pRecipe | pCompartment ) + pModel

# yacmlBNF_ = OneOrMore( pCompartment )
yacmlBNF_.setParseAction( parser_main )
yacmlBNF_.ignore( javaStyleComment )
#yacmlBNF_.setDebug( )
