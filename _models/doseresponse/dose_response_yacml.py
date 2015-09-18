#########################################################################
## This program is part of 'MOOSE', the
## Messaging Object Oriented Simulation Environment.
##           Copyright (C) 2013 Upinder S. Bhalla. and NCBS
## It is made available under the terms of the
## GNU Lesser General Public License version 2.1
## See the file COPYING.LIB for the full notice.
#########################################################################

import math
import pylab
import numpy
import moose

import sys
sys.path.append('../..')
import yacml
import moose

def extra():
    state = moose.SteadyState( '/model/compt/state' )
    state.stoich = moose.wildcardFind('/model/compt/##[TYPE=Stoich]')[0]

    state.convergenceCriterion = 1e-6
    moose.seed( 111 ) # Used when generating the samples in state space

    b = moose.element( '/model/compt/b' )
    a = moose.element( '/model/compt/a' )
    c = moose.element( '/model/compt/c' )
    a.concInit = 0.1
    deltaA = 0.002
    num = 150
    avec = []
    bvec = []
    moose.reinit()

    # Now go up.
    for i in range( 0, num ):
        moose.start( 1.0 ) # Run the model for 1 seconds.
        state.settle() # This function finds the steady states.
        avec.append( a.conc )
        bvec.append( b.conc )
        a.concInit += deltaA
        #print i, a.conc, b.conc
    pylab.plot( numpy.log10( avec ), numpy.log10( bvec ), label='b vs a up' )
    # Now go down.
    avec = []
    bvec = []
    for i in range( 0, num ):
        moose.start( 1.0 ) # Run the model for 1 seconds.
        state.settle() # This function finds the steady states.
        avec.append( a.conc )
        bvec.append( b.conc )
        a.concInit -= deltaA
        #print i, a.conc, b.conc


    pylab.plot( numpy.log10( avec ), numpy.log10( bvec ), label='b vs a down' )
    # Now aim for the middle. We do this by judiciously choosing a 
    # start point that should be closer to the unstable fixed point.
    avec = []
    bvec = []
    a.concInit = 0.28
    b.conc = 0.15
    for i in range( 0, 65 ):
        moose.start( 1.0 ) # Run the model for 1 seconds.
        state.settle() # This function finds the steady states.
        avec.append( a.conc )
        bvec.append( b.conc )
        a.concInit -= deltaA
        #print i, a.conc, b.conc
    pylab.plot( numpy.log10( avec ), numpy.log10( bvec ), label='b vs a mid' )

    pylab.ylim( [-1.7, 1.2] )
    pylab.legend()
    pylab.show()
    quit()


def main():
    modelfile = "./model.yacml"
    model = yacml.loadYACML(modelfile)
    extra()
    model.run()

if __name__ == '__main__':
    main()
