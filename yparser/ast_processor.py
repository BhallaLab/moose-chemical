"""flattenedAST_processpr.py: 

Process the ast of YACML.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import lxml.etree as etree
from copy import deepcopy
from config import logger_

flattenedAST_ = etree.Element( 'yacml' )

def find_recipe( doc, recipe_id ):
    recipe = doc.xpath( '/yacml/recipe[@id="%s"]' % recipe_id )
    if not recipe:
        msg = 'Could not find any recipe with name %s' % recipe_id 
        msg +=  '\t I cannot continue ' 
        raise NameError( msg )
    assert len(recipe) == 1, "Found more the 1 recipe with id %s" % recipe_id
    return recipe[0]

def find_reaction( rootXML, reaction_id ):
    rXML = rootXML.xpath( '//reaction_declaration[@id="%s"]' % reaction_id )
    if not rXML:
        msg = 'Could not find any reaction with name %s' % reaction_id
        msg +=  '\t I cannot continue ' 
        raise NameError( msg )
    assert len( rXML ) == 1, 'Found more the 1 reaction with id %s' % reaction_id
    return rXML[0]

def find_compartment( rootXML, compt_id ):
    cXML = rootXML.xpath( 'compartment[@id="%s"]' % compt_id )
    if not cXML:
        msg = 'Could not find any compartment with name %s' % compt_id
        msg +=  '\t I cannot continue ' 
        raise NameError( msg )

    assert len( cXML ) == 1, 'Found more the 1 compartment with id %s' % compt_id
    logger_.debug( 'Found declaration of compartment with type %s' % compt_id )
    return cXML[0]

def replace_all( from_list, reduce_list ):
    somethingToReplace = False
    while from_list:
        r = from_list.pop()
        rName = r.attrib['name']
        for var in reduce_list:
            if rName in var.text:
                somethingToReplace = True
                var.text = var.text.replace( rName, r.text )
                try:
                    var.text = str( eval( var.text ) )
                    var.attrib['is_reduced'] = 'true' 
                except Exception as e:
                    pass
    return somethingToReplace

def replace_local_variables( recipe_xml, doc, others = [] ):
    logger_.debug( 'Replacing local variables' )
    reduced = recipe_xml.xpath( 'variable[@is_reduced="true"]' )
    unreduced = recipe_xml.xpath( '//variable[@is_reduced="false"]' )
    localVars = reduced + others
    somethingToReplace = replace_all( reduced + others, unreduced )
    if somethingToReplace:
        replace_local_variables( recipe_xml, doc, others )

def flatten_compartment_expression( compt_xml ):
    # Flatten as many expression as we can.
    geomVar = compt_xml.xpath( 'geometry/variable' )
    reducedVars = compt_xml.xpath( 'variable[@is_reduced="true"]' )
    unreducedVars = compt_xml.xpath( 
            'chemical_reaction_subnetwork/variable[@is_reduced="false"]' 
            )
    somethingToReplace = replace_all( geomVar + reducedVars, unreducedVars )
    if somethingToReplace:
        flatten_compartment_expression( compt_xml )


##
# @brief Flatten a compartment.
#
# @param comptXML
# @param doc
#
# @return 
def flatten_compartment( comptXML, doc ):
    global flattenedAST_

    flattenComptXML = etree.SubElement( flattenedAST_, 'compartment' )
    # Attach the attributes.
    for atb in comptXML.attrib:
        flattenComptXML.attrib[ atb ] = comptXML.attrib[ atb ]

    # Attach geometry
    for geomXML in comptXML.xpath( 'geometry' ):
        flattenComptXML.append( deepcopy( geomXML ) )

    # attach variable.
    for varXML in comptXML.xpath( 'variable' ):
        flattenComptXML.append( deepcopy( varXML ) )

    # Fix the recipe instances.
    recipeInsts = comptXML.findall( 'recipe_instance' )
    for recipeI in recipeInsts:
        logger_.info( 'Replacing recipe instance of %s' % recipeI.text )
        instOf = recipeI.attrib['instance_of']
        recipe = find_recipe( doc, instOf )
        netXML = etree.SubElement( flattenComptXML, 'chemical_reaction_subnetwork' )
        netXML.attrib['type'] = instOf
        netXML.attrib['name'] = recipeI.text
        [ netXML.append( deepcopy(c) ) for c in recipe ]
        # flatten_compartment_expression( flattenComptXML )

##
# @brief Flatten the declaration of recipe. Replace all the local variables.
#
# @param recipeXML
# @param doc
#
# @return 
def flatten_recipe( recipeXML, doc ):
    replace_local_variables( recipeXML, doc )
    reactionInstances = recipeXML.xpath( '//reaction[@instance_of]' )
    for reac in reactionInstances:
        instOf = reac.attrib['instance_of']
        rXML = find_reaction( recipeXML, instOf )
        [ reac.append( deepcopy( elem ) ) for elem in rXML ]

##
# @brief Flatten a given model XML element.
#
# @param model_xml
#
# @return XML element representing model.
def flatten_model( model_xml, ast ):
    global flattenedAST_
    yacmlXML = etree.Element( 'yacml' )
    modelXML = etree.SubElement( yacmlXML, 'model' )
    for atb in model_xml.attrib:
        modelXML.attrib[atb] = model_xml.attrib[ atb ]

    # The compartments are flattened and stored in flattenedAST_ 
    for compt in model_xml.xpath( 'compartment_instance' ):
        instName = compt.text
        instOf = compt.attrib['instance_of']
        comptInst = find_compartment( flattenedAST_, instOf )
        comptInst.attrib.update( compt.attrib )
        # Add/update old attributes which may not be relevant to declaration 
        comptInst.attrib['name'] = instName
        comptInst.attrib['instance_of'] = comptInst.attrib['id']
        # Note: Don't delete 'id' attrib from dictionary
        modelXML.append( deepcopy( comptInst ) )
    return yacmlXML


##
# @brief This function does the following:
#    - Replaces each instance of recipe in compartment with inline xml code.
#
# @param ast
#
# @return modified AST. Structure of AST does not change at all.
def flatten( ast ):
    global flattenedAST_
    # Rewrite AST.
    # recipes = ast.xpath( '/yacml/recipe' )
    # [ flatten_recipe( r, ast ) for r in recipes ]
    compts = ast.xpath( '/yacml/compartment' )
    [ flatten_compartment( c, ast ) for c in compts ]

    # And finally flatten the model. This is the last 
    model = ast.find( 'model' )
    flattenModel = flatten_model( model, ast )

    return flattenModel
