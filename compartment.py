"""compartment.py: 

Compartment class representing geometry where DOT model is loaded.

NOTE: currently not being used.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh "
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


class Compartment(object):
    """Compartment where reaction happens"""

    def __init__(self, id):
        super(Compartment, self).__init__()
        self.id = id 
        self.name = None
        self.geometry = None 
        self.mooseObject = None
        
        
