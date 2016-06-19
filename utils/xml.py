"""xml.py: 

Helper function to deal with lxml.


"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

from config import logger_

def get_value_from_parameter_xml( param_elem, param_name ):
    elem = param_elem.xpath( 'parameter[@name="%s"]' % param_name )
    if not elem:
        return None
    else:
        return float( elem[0].text )

def get_value_from_variable_xml( root_xml, param_name ):
    elem = root_xml.xpath( 'variable[@name="%s"]' % param_name )
    if len(elem) == 0:
        logger_.warn( 'Could not find paramter %s. Using 0' % param_name )
        return 0.0
    else:
        return float( elem[0].text )

def find_reaction_instance( root_xml, rname ):
    reacInsts =  root_xml.xpath( 'reaction_declaration[@id="%s"]' % rname )
    if not reacInsts:
        logger_.warn( 'I could not find a reaction declaration %s ' % rname )

    assert len( reacInsts ) == 1, 'More than one definition of %s' % rname 
    return reacInsts[0]

