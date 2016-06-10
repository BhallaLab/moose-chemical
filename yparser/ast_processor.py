"""ast_processpr.py: 

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


##
# @brief Flatten a compartment.
#
# @param comptXML
# @param doc
#
# @return 
def flatten_compartment( comptXML, doc ):
    # Replace instance of each recipe by inline xml.
    recipeInsts = comptXML.findall( 'recipe_instance' )
    toReplace = {}
    for recipeI in recipeInsts:
        instOf = recipeI.attrib['instance_of']
        recipe = find_recipe( doc, instOf )
        network = etree.SubElement( comptXML, 'chemical_reaction_subnetwork' )
        network.attrib['type'] = instOf
        nameElem = etree.SubElement( network, 'name' )
        nameElem.text = recipeI.text
        [ network.append( c ) for c in recipe ]

def flatten_recipe( recipeXML, doc ):
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
    # Rewrite AST.
    recipes = ast.xpath( '/yacml/recipe' )
    [ flatten_recipe( r, ast ) for r in recipes ]
    compts = ast.xpath( '/yacml/compartment' )
    [ flatten_compartment( c, ast ) for c in compts ]
    return ast
