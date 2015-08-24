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
    t.connect('requestOut', elem, 'getN')
    records_[elem.name] = t

def make_model():
    compt = moose.CubeMesh('/compartment')
    compt.volume = 1e-20
    a = moose.Pool('/compartment/a')
    b = moose.Pool('/compartment/b')
    a.nInit, b.nInit = 300, 100
    c = moose.Pool('/compartment/c')
    c.nInit = 0
    for x in [a, b, c]:
        add_table(x)
    reac = moose.Reac('/reac')
    reac.connect('sub', a, 'reac')
    reac.connect('sub', b, 'reac')
    reac.connect('prd', c, 'reac')
    reac.Kf = 50
    reac.Kb = 0.4
    return compt

def setup_solver(compt):
    gsolve = moose.Gsolve('/compartment/gsolve')
    stoich = moose.Stoich('/compartment/stoich')
    stoich.compartment = compt
    stoich.ksolve = gsolve
    stoich.path = '/compartment/##'

def main():
    global records_
    compt = make_model()
    setup_solver(compt)
    moose.reinit()
    moose.start(50)
    mu.plotRecords( records_ )

if __name__ == '__main__':
    main()
