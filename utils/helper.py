"""helper.py

Helper functions.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

def to_bool(arg):
    if arg.lower() in [ "0", "false", "no" ]:
        return False
    return True

def to_float(string):
    """Convert a given string to float """
    string = string.replace('"', '')
    return float(eval(string))


