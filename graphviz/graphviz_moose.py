"""graph_chem.py: 

    Load a graphviz chemical model into MOOSE.

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
import pylab
import numpy
import graphviz_to_chemical as util
import sys
import moose.utils as mu

_global = {}
_plots = {}
_data = {}

def setupModel(dot_file, sbml_file):
    dotModel = util.DotModel(dot_file)
    dotModel.load()
    return dotModel

def setupSolvers():
    ksolve = moose.Ksolve('/ksolve')
    stoich = moose.Stoich('/stoich')
    stoich.ksolve = ksolve
    stoich.path = '/##'

def main(args):
    modelFile = args.model_file
    outfile = modelFile.replace(".dot", ".xml")
    model = setupModel(modelFile, outfile)
    #setupSolvers()
    moose.reinit()
    moose.start(args.sim_time)

    tables = model.tables
    mu.plotTables(tables, outfile="kinetic.png")

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''parser'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--sim_time', '-st', metavar='variable'
        , required = True
        , type = float
        , help = 'A generic option'
        )
    parser.add_argument('--model_file', '-f'
        , required = True
        , type = str
        , help = 'Model file'
        )
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main(args)
