"""test_solve.py: 

A model with three species in a very small number of molecules.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import moose
import moose.utils as mu

records_ = {}

def add_table(elem):
    global records_
    t = moose.Table2('%s/table' % elem.path)
    t.connect('requestOut', elem, 'getConc')
    records_[elem.name] = t

def make_model():
    compt = moose.CubeMesh('/compartment')
    compt.volume = 1e-20
    a = moose.Pool('/compartment/a')
    b = moose.Pool('/compartment/b')
    a.nInit, b.nInit = 30, 10
    c = moose.Pool('/compartment/c')
    c.nInit = 0
    for x in [a, b, c]:
        add_table(x)
    reac = moose.Reac('/reac')
    reac.connect('sub', a, 'reac')
    reac.connect('sub', b, 'reac')
    reac.connect('prd', c, 'reac')
    reac.Kf = 3.0
    reac.Kb = 1.0

def setup_solver():
    gsolve = moose.Gsolve('/gsolve')
    stoich = moose.Stoich('/stoich')
    stoich.compartment = moose.Compartment('/compartment')
    stoich.ksolve = gsolve
    stoich.path = '/compartment/##'

def main():
    global records_
    make_model()
    setup_solver()
    moose.reinit()
    moose.start(30)
    mu.plotRecords( records_ )

if __name__ == '__main__':
    main()
