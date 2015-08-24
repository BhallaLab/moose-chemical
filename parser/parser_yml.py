"""parser_yml.py: 

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import yaml
import sys

def parse(filename, **kwargs):
    model = None
    print("Loading %s" % filename)
    with open(filename, "r") as f:
        model = yaml.load(f)
    assert model
    return model

if __name__ == '__main__':
    filename = sys.argv[1]
    print parse(filename)
