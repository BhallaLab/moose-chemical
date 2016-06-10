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
    global flattenedAST_
    rXML = rootXML.xpath( '//reaction_declaration[@id="%s"]' % reaction_id )
    if not rXML:
        msg = 'Could not find any reaction with name %s' % reaction_id
        msg +=  '\t I cannot continue ' 
        raise NameError( msg )
    assert len( rXML ) == 1, 'Found more the 1 reaction with id %s' % reaction_id
    return rXML[0]

def replace_all( from_list, reduce_list ):
    # Reduce 
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

def local_variables( recipe_xml, doc, others = [] ):
    print( '[DEBUG] Replacing local variables' )
    reduced = recipe_xml.xpath( 'variable[@is_reduced="true"]' )
    unreduced = recipe_xml.xpath( '//variable[@is_reduced="false"]' )
    localVars = reduced + others
    somethingToReplace = replace_all( reduced + others, unreduced )
    if somethingToReplace:
        local_variables( recipe_xml, doc, others )

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
    # Replace instance of each recipe by inline xml.
    flattenComptXML = etree.SubElement( flattenedAST_, 'compartment' )

    # Attach geometry
    for geomXML in comptXML.xpath( 'geometry' ):
        flattenComptXML.append( deepcopy( geomXML ) )

    # attach variable.
    for varXML in comptXML.xpath( 'variable' ):
        flattenComptXML.append( deepcopy( varXML ) )

    # Fix the recipe instances.
    recipeInsts = comptXML.findall( 'recipe_instance' )
    for recipeI in recipeInsts:
        print( '[INFO] Replacing recipe instance of %s' % recipeI.text )
        instOf = recipeI.attrib['instance_of']
        recipe = find_recipe( doc, instOf )
        netXML = etree.SubElement( flattenComptXML, 'chemical_reaction_subnetwork' )
        netXML.attrib['type'] = instOf
        nameElem = etree.SubElement( netXML, 'name' )
        nameElem.text = recipeI.text
        [ netXML.append( deepcopy(c) ) for c in recipe ]
        flatten_compartment_expression( flattenComptXML )

##
# @brief Flatten the declaration of recipe. Replace all the local variables.
#
# @param recipeXML
# @param doc
#
# @return 
def flatten_recipe( recipeXML, doc ):
    local_variables( recipeXML, doc )
    reactionsWithId = recipeXML.xpath( '//reaction[@instance_of]' )
    for reac in reactionsWithId:
        instOf = reac.attrib['instance_of']
        rXML = find_reaction( recipeXML, instOf )
        [ reac.append( elem ) for elem in rXML ]
        del reac.attrib['instance_of']


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
    recipes = ast.xpath( '/yacml/recipe' )
    [ flatten_recipe( r, ast ) for r in recipes ]
    compts = ast.xpath( '/yacml/compartment' )
    [ flatten_compartment( c, ast ) for c in compts ]
    return flattenedAST_
