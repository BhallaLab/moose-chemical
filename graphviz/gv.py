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
import moose.utils as mu
import ast
import re
import operator as ops
import sys
from collections import defaultdict
import reaction
import tempfile
import matplotlib.pyplot as plt

import logging
logger_ = logging.getLogger('gv.graphviz')
logger_.setLevel(logging.DEBUG)


class DotModel():
    '''
    Parse graphviz file and populate a chemical model in MOOSE.
    '''

    def __init__(self, modelFile):
        self.filename = modelFile
        self.G = nx.MultiDiGraph()
        self.molecules = {}
        self.reactions = {}
        self.kinetics = {}
        self.functions = {}
        self.poolPath = '/pool'
        self.modelPath = '/model'
        self.funcPath = '/function'
        self.variables = {}
        self.tables = {}
        self.load()

    def init_moose(self, compt):
        """Initialize paths in MOOSE"""
        for path in [self.poolPath, self.funcPath, self.modelPath]:
            moose.Neutral(path)

        if compt is None:
            self.compartment = moose.CubeMesh('/compartment')
        else: self.compartment = compt
        self.poolPath = self.compartment.path

    def attach_types(self):
        """This function attach types to node of graphs"""
        npools, nbufpools, nreacs = 0, 0, 0
        for n in self.G.nodes():
            attr = self.G.node[n]
            if "conc_init" in attr.keys():
                self.G.node[n]['type'] = 'pool'
                npools += 1
            elif 'n_init' in attr.keys():
                self.G.node[n]['type'] = 'pool'
                npools += 1
            elif 'expr' in attr.keys() or 'kf' in attr.keys():
                self.G.node[n]['type'] = 'reaction'
                self.G.node[n]['shape'] = 'rect'
                nreacs += 1
            else:
                logger_.warning("Unknown node type: %s" % n)

            if attr.get('buffered', 'false') == 'true':
                self.G.node[n]['type'] = 'bufpool'
                nbufpools += 1

        logger_.info("Reactions = {0}, Pools(buffered) = {1}({2})".format(
            nreacs , npools , nbufpools))

    def create_graph(self):
        """Create chemical network """
        self.G = nx.read_dot(self.filename)
        self.G = nx.MultiDiGraph(self.G)
        assert self.G.number_of_nodes() > 0, "Zero molecules"
        self.attach_types()

    def checkNode(self, n):
        return True

    def checkEdge(self, src, tgt):
        return True

    def load(self, compt = None):
        '''Load given model into MOOSE'''

        self.init_moose(compt)
        self.create_graph()

        compt = moose.CubeMesh('%s/mesh_comp' % self.modelPath)
        compt.volume = float(self.G.graph['graph']['volume'])
        # Each node is molecule in graph.
        for node in self.G.nodes():
            attr = self.G.node[node]
            print attr['type']
            if attr['type'] in ['pool', 'bufpool']:
                self.checkNode(node)
                self.add_molecule(node, compt)
            elif attr['type'].lower() == 'reaction':
                self.add_reaction(node, compt)
            else:
                warnings.warn("Unknown/Unsupported type of node in graph")
        # Dump the edited graph into a temp file.
        outfile = '%s_out.dot' % self.filename
        logger_.debug("Writing network to : %s" % outfile)
        nx.write_dot(self.G, outfile)

    def add_molecule(self, molecule, compt):
        '''Load node of graph into MOOSE'''

        moleculeDict = self.G.node[molecule]
        poolPath = '{}/{}'.format(compt.path, molecule)
        moleculeType = moleculeDict['type']

        logger_.debug("Adding molecule %s" % molecule)
        logger_.debug("+ With params: %s" % moleculeDict)

        if moleculeType == 'pool':
            p = self.add_pool(poolPath, molecule, moleculeDict)
        elif "bufpool" == moleculeType:
            self.add_bufpool(poolPath, molecule, moleculeDict)
        elif "enzyme" == moleculeType:
            self.addEnzyme(poolPath, molecule, moleculeDict)

        # Attach a table to it.
        if moleculeDict.get('plot', 'false').lower() != 'false':
            self.add_recorder(molecule)

    def add_expr_to_function(self, expr, func):
        """Reformat a given expression 

        Attach a expression to given function.

        Also connect y0, y1 etc to molecules.
        """
        transDict = {}
        astExpr = ast.parse(expr)
        i = 0
        for node in ast.walk(astExpr):
            if type(node) == ast.Name:
                if self.molecules.get(node.id, None) is not None:
                    key, val = 'y%s' %i, self.molecules[node.id]
                    expr = expr.replace(node.id, key)
                    transDict[key] = val
                    i += 1
        logger_.debug("Adding expression: %s" % expr)
        func.expr = expr
        for k in transDict:
            logger_.debug("Connecting %s with %s" % (k, transDict[k]))
            moose.connect(func, 'requestOut', transDict[k], 'getConc')


    def add_forward_rate_expr(self, reac, expr):
        """Add an expression for forward rate constant"""
        logger_.debug("++ Forward rate expression: %s" % expr)
        funcPath = '%s/forward_expr_f' % reac.path
        forwardExprFunc = moose.Function(funcPath)
        self.add_expr_to_function(expr, forwardExprFunc)
        logger_.debug("Setting Kf of reac:%s, func:%s" % (reac, forwardExprFunc))
        moose.connect(forwardExprFunc, 'valueOut', reac, 'setKf') 

    def add_backward_rate_expr(self, reac, expr):
        """Add an expression for backward rate constant
        """
        logger_.debug("++ Backward rate expression: %s" % expr)
        funcPath = '%s/backward_expr_f' % reac.path
        backwardFunction = moose.Function(funcPath)
        self.add_expr_to_function(expr, backwardFunction)
        logger_.debug("Setting Kb of reac:%s, func:%s" % (reac, backwardFunction))
        moose.connect(backwardFunction, 'valueOut', reac, 'setKb') 

    def add_reaction_attr(self, reac, attr):
        """Add attributes to reaction.
        """
        kf = attr['kf']
        kb = attr.get('kb', 0.0)
        try:
            kf = float(kf)
            reac.Kf = kf
        except Exception as e:
            self.add_forward_rate_expr(reac, kf)

        try:
            kb = float(kb)
            reac.Kb = kb
        except Exception as e:
            self.add_backward_rate_expr(reac, kb)


    def add_reaction(self, node, compt):
        """Add a reaction node to MOOSE"""
        attr = self.G.node[node]
        logger_.info("|- Adding a reaction: %s" % attr)
        reacName = node
        reacPath = '%s/%s' % (compt.path, reacName)
        reac = moose.Reac(reacPath)
        self.reactions[node] = reac
        self.add_reaction_attr(reac, attr)
        for sub, tgt in self.G.in_edges(node):
            logger_.debug("Adding sub to reac: %s" % sub)
            moose.connect(reac, 'sub', self.molecules[sub], 'reac')
        for sub, tgt in self.G.out_edges(node):
            logger_.debug("Adding prd to reac: %s" % tgt)
            moose.connect(reac, 'prd', self.molecules[tgt], 'reac')

    def add_pool(self, poolPath, molecule, moleculeDict):
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

    def add_bufpool(self, poolPath, molecule, moleculeDict):
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

    def add_recorder(self, molecule):
        # Add a table
        logger_.info("Adding a Table on : %s" % molecule)
        moose.Neutral('/tables')
        tablePath = '/tables/{}'.format(molecule)
        tab = moose.Table(tablePath)
        elemPath = self.molecules[molecule]
        tab.connect('requestOut', elemPath, 'getConc')
        self.tables[molecule] = tab
        return elemPath

    def run(self, args):
        """
        Run model with given parameters.

        sim_time = simulation time
        outfile = File to save the results.
        """
        for i in range(10, 16):
            moose.setClock(i, 1e-2)
        moose.reinit()
        logger_.info("Running MOOSE for %s" % args['sim_time'])
        moose.start(float(args['sim_time']))
        if args['outfile']:
            mu.saveRecords(self.tables
                    , outfile = args['outfile']
                    , subplot = True
                    )

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
