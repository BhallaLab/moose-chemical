"""bnf_helper.py: 

Functions to load YACML into MOOSE.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import os
from config import logger_
import lxml.etree as etree

# Current context of parser. It 
root_ = etree.Element( 'yacml' )
recipes_ = etree.SubElement( root_, 'recipes' )
compts_ = etree.SubElement( root_, 'compartments' )
model_ = etree.SubElement( root_, 'model' )

class Context():

    """Parser context"""

    def __init__(self):
        self.context = None 
        self.params = {}
        

context_ = Context()


def add_species( tokens ):
    print( '[INFO] Species, tokens %s' % tokens )


def set_context( tokens ):
    print( '[DEBUG] Setting context %s' % tokens )
    context_.context = 'model'

def add_recipe( tokens ):
    logger_.debug( '[INFO] Setting up recipe with tokens %s' % tokens )
    print( 'Adding recipe' )


def set_recipe_name( tokens ):
    global recipes_
    logger_.debug( 'Setting up recipe name ' )
    recipe = etree.SubElement( recipes_, 'recipe' )
    recipe.text = tokens[0]


def set_recipe_begin( tokens ):
    logger_.debug( 'New recipe found ' )
