"""util.py: 

    Generates a SBML model.
"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


import networkx as nx
import warnings
import moose
import ast
import re
import operator as ops
import sys
from config import logger_
from collections import defaultdict
import reaction


class DotModel():
    '''
    Parse graphviz file and populate a chemical model in MOOSE.
    '''

    def __init__(self, modelFile):
        self.filename = modelFile
        self.G = nx.DiGraph()
        self.molecules = {}
        self.reactions = {}
        self.kinetics = {}
        self.functions = {}
        self.poolPath = '/pool'
        self.reacPath = '/reac'
        self.modelPath = '/model'
        self.funcPath = '/function'
        self.variables = {}
        self.tables = {}

    def initMOOSE(self, compt):
        """Initialize paths in MOOSE"""
        for path in [self.poolPath, self.funcPath, self.reacPath, self.modelPath]:
            moose.Neutral(path)

        if compt is None:
            self.compartment = moose.CubeMesh('/compartment')
        else: self.compartment = compt
        self.poolPath = self.compartment.path

    def createNetwork(self):
        """Create chemical network """
        self.G = nx.read_dot(self.filename)
        # We don't want MultiDiGraph.
        self.G = nx.DiGraph(self.G)
        assert self.G.number_of_nodes() > 0, "Zero molecules"

    def checkNode(self, n):
        return True

    def checkEdge(self, src, tgt):
        return True

    def find_reactions(self):
        """Find all reactions in graph. 
        Return a dictionary.
        """
        reacs = reaction.ReactionsSet(self.G)
        for e in self.G.edges():
            reacs.add_reaction(e, self.G)
        logger_.info("Total of %s raections found" % len(reacs))
        return reacs

    def load(self, compt = None):
        '''Load given model into MOOSE'''

        self.initMOOSE(compt)
        self.createNetwork()
        moose.Neutral('/pool')
        compt = moose.CubeMesh('%s/mesh_comp' % self.modelPath)
        compt.volume = float(self.G.graph['graph']['volume'])

        # Each node is molecule in graph.
        for molecule in self.G.nodes():
            self.checkNode(molecule)
            self.addMolecule(molecule, compt)

        # Find reactions with label l. Each reaction can have more than one
        # edges.
        reactionSet = self.find_reactions()
        for s in reactionSet:
            reactionSet[s].insert_into_moose(
                    "%s/%s" % (self.reacPath, s)
                    , self.molecules
                    )
        quit()

            
    def addMolecule(self, molecule, compt):
        '''Load node of graph into MOOSE'''

        moleculeDict = self.G.node[molecule]
        poolPath = '{}/{}'.format(compt.path, molecule)

        moleculeType = moleculeDict.get('type', None)
        logger_.debug("Adding molecule %s" % molecule)
        logger_.debug("+ With params: %s" % moleculeDict)

        if not moleculeType:
            p = self.addPool(poolPath, molecule, moleculeDict)
        elif "constant" == moleculeType:
            self.addBufPool(poolPath, molecule, moleculeDict)
        elif "enzyme" == moleculeType:
            self.addEnzyme(poolPath, molecule, moleculeDict)

        # Attach a table to it.
        self.addRecorder(molecule)


    def addPool(self, poolPath, molecule, moleculeDict):
        """Add a moose.Pool or moose.BufPool to moose for a given molecule """

        if moleculeDict.get('type', 'variable') == 'constant':
            p = moose.BufPool(poolPath)
        else:
            p = moose.Pool(poolPath)

        concInit = moleculeDict.get('conc_init', 0.0)
        p.concInit = float(concInit)
        if moleculeDict.get('n_init', None):
            p.nInit = float(moleculeDict['n_init'])

        self.molecules[molecule] = p
        return p

    def addBufPool(self, poolPath, molecule, moleculeDict):
        """Add a moose.Pool or moose.BufPool to moose for a given molecule """

        p = moose.BufPool(poolPath)
        concInit = moleculeDict.get('conc_init', 0.0)
        p.concInit = float(concInit)
        if moleculeDict.get('n_init', None):
            p.nInit = float(moleculeDict['n_init'])
        self.molecules[molecule] = p
        return p

    def addEnzyme(self, poolPath, molecule, moleculeDict):
        """Add an enzyme """
        enz =  moose.Enz(poolPath)
        enz.concInit = float(moleculeDict.get('conc_init', 0.0))
        self.molecules[molecule] = enz
        self.enzymes[molecule] = enz
        return enz

    def addRecorder(self, molecule):
        # Add a table
        moose.Neutral('/tables')
        tablePath = '/tables/{}'.format(molecule)
        tab = moose.Table(tablePath)
        elemPath = self.molecules[molecule]
        tab.connect('requestOut', elemPath, 'getConc')
        self.tables[molecule] = tab
        return elemPath

def writeSBMLModel(dot_file, outfile = None):
    model = DotModel(dot_file)
    model.createNetwork()
    model.writeSBML(outfile)

def main():
    writeSBMLModel(dot_file = "./smolen_baxter_bryne.dot"
            , outfile = "smolen_baxter_bryne.sbml"
            )

if __name__ == '__main__':
    main()
