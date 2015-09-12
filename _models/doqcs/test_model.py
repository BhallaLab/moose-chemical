#!/usr/bin/env python
"""test_model.py: 

    Some test function to test the kkit model.
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
import sys
import moose.kkit as kkit
import pylab

moose.Neutral('/model')

def main():
    modelname = sys.argv[1]
    modelType = modelname.split(".")[-1]
    if modelType == "xml":
        model = moose.readSBML(modelname, '/model')
    else:
        #kkit.visualize(modelname)
        model = moose.loadModel(modelname, '/model', 'gssa')
    tables = moose.wildcardFind('/##[TYPE=Table2]')
    records = {}
    for t in tables: records[t.path.split('/')[-1]] = t

    c = moose.Clock('/clock')
    #for i in range(10, 16):
    #    moose.setClock(i, 0.001)

    moose.reinit()
    moose.start(200)

    outfile = '%s.png' % modelname
    mu.plotRecords(records, subplot=True, outfile=outfile)

if __name__ == '__main__':
    main()
