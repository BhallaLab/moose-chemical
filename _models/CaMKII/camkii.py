"""camkii.py: 

    A test script for modelling CaMKII model.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import sys
sys.path.append('../..')
import yacml
import moose

def add_extra(model):
    """Add extra information to model
    """
    ca = model.molecules['ca']
    caIn = moose.PulseGen('%s/ca_pulse' % ca.path)
    caIn.level[0] = 1e-3
    caIn.baseLevel = 1e-4
    caIn.delay[0] = 10
    caIn.delay[1] = 200
    caIn.width[0] = 200
    moose.connect(caIn, 'output', ca, 'setConc')
    moose.reinit()

def main():
    modelfile = "camkii.yacml"
    model = yacml.loadYACML(modelfile)
    #add_extra(model)
    model.run()

if __name__ == '__main__':
    main()
