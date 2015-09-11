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
from utils import test_expr as te
import operator as ops
import sys
from collections import defaultdict
import reaction
import tempfile
import matplotlib.pyplot as plt

import logging
logger_ = logging.getLogger('loader.chemviz')
logger_.setLevel(logging.DEBUG)

def yacml_to_dot(text):
    """yacml_to_dot
    Convert YACML test to a dot.

    :param text: Text of YACML model.
    """
    text = text.replace('compartment', 'digraph')
    return text

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
        self.poolPath = None
        self.modelPath = '/model'
        self.funcPath = None
        self.variables = {}
        self.tables = {}
        self.nodes_with_tests = []
        self.compartments = {}
        self.__cwd__ = ""
        self.__cur_compt__ = None
        # Finally load the model
        self.load()

    def init_moose(self, compt):
        """Initialize paths in MOOSE"""
        for path in [self.modelPath]:
            moose.Neutral(path)

        comptName = str(self.G)

        curCompt = None
        if compt is None:
            logger_.info("Creating compartment: %s" % comptName)
            curCompt =  moose.CubeMesh('%s/%s' % (self.modelPath, comptName))
        else: 
            curCompt = compt

        self.compartments[comptName] = curCompt
        self.poolPath = curCompt.path
        self.__cwd__ = curCompt.path
        self.__cur_compt__ = curCompt

    def attach_types(self):
        """This function attach types to node of graphs"""
        npools, nbufpools, nreacs = 0, 0, 0
        for n in self.G.nodes():
            attr = self.G.node[n]

            self.G.node[n]['do_test'] = False
            for k in attr.keys():
                if "test" in k: 
                    self.G.node[n]['do_test'] = True

            if "conc_init" in attr.keys() or 'conc' in attr.keys():
                self.G.node[n]['type'] = 'pool'
                npools += 1
            elif 'n_init' in attr.keys() or 'n' in attr.keys():
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

        with tempfile.NamedTemporaryFile( delete = False , suffix = '.dot') as dotFile:
            with open(self.filename, "r") as f:
                modelText = f.read()
            logger_.debug("Generating graphviz : %s" % dotFile.name)
            dotFile.write(yacml_to_dot(modelText))
            dotFile.flush()
            try:
                self.G = nx.read_dot(dotFile.name)
            except Exception as e:
                mu.error(["Failed to load YACML file." 
                    , "Error was %s" % e
                    ])

        self.G = nx.MultiDiGraph(self.G)
        assert self.G.number_of_nodes() > 0, "Zero molecules"
        self.attach_types()


    def checkNode(self, n):
        return True

    def checkEdge(self, src, tgt):
        return True

    def load(self, compt = None):
        '''Load given model into MOOSE'''

        self.create_graph()
        self.init_moose(compt)

        compt = self.__cur_compt__ 
        compt.volume = float(self.G.graph['graph']['volume'])
        # Each node is molecule in graph.
        for node in self.G.nodes():
            attr = self.G.node[node]
            if attr['type'] in ['pool', 'bufpool']:
                self.checkNode(node)
                self.add_molecule(node, compt)
            elif attr['type'].lower() == 'reaction':
                self.add_reaction(node, compt)
            else:
                warnings.warn("Unknown/Unsupported type of node in graph")
        # Dump the edited graph into a temp file.
        outfile = '%s.dot' % self.filename
        logger_.debug("Writing network to : %s" % outfile)
        nx.write_dot(self.G, outfile)

    def add_molecule(self, molecule, compt):
        """add_molecule
        add molecule to compartment.

        :param molecule: name of the molecule to add.
        :param compt: Under which comparment to add.
        """

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
            f = 'conc'
            if 'n_init' in moleculeDict or 'n' in moleculeDict: 
                f = 'n'
            self.add_recorder(molecule, f)

        if moleculeDict['do_test']:
            self.add_test(molecule)

    def add_expr_to_function(self, expr, func, field = 'conc'):
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
            f = 'get' + field[0].upper() + field[1:]
            moose.connect(func, 'requestOut', transDict[k], f)


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

        # Check for solvers.
        if attr.get('solver', None) is not None:
            self.setup_solver(reac, attr['solver'])

    def setup_solver(self, reac, solver):
        """setup_solver. Use a solver for given reaction.

        :param reac: moose.Reaction element.
        :param solver: Type of solver, string.
        """
        if solver == 'stoich':
            mu.info("Creating a sotich solver on %s" % reac.name)
            logger_.debug("reac: %s" % reac)
            logger_.debug("Compt: %s" % self.__cur_compt__)
            if not moose.exists('%s/gsolve' % self.__cwd__):
                gsolve = moose.Gsolve('%s/gsolve' % self.__cwd__)
                stoich = moose.Stoich('%s/stoich' % self.__cwd__)
                stoich.compartment = self.__cur_compt__ 
                stoich.ksolve = gsolve
                if stoich.path != "%s/##" % self.__cwd__:
                    stoich.path = '%s/##' % self.__cwd__
            else:
                mu.warn("Gsolve already exists. Not creating a new one.")
        else:
            mu.warn("Solver type %s is unknown/unsuppored" % solver)


    def add_pool(self, poolPath, molecule, moleculeDict):
        """Add a moose.Pool or moose.BufPool to moose for a given molecule """

        if moleculeDict.get('type', 'variable') == 'constant':
            p = moose.BufPool(poolPath)
        else:
            p = moose.Pool(poolPath)

        if 'conc_init' in moleculeDict:
            concInit = float(moleculeDict['conc_init'])
            logger_.debug("Setting %s.conc_init to %s" % (molecule, concInit))
            p.concInit = concInit
        elif 'n_init' in  moleculeDict:
            p.nInit = float(moleculeDict['n_init'])
        else:
            mu.fatal("Neither conc_init nor n_init specified for %s" % molecule)

        # If there is an expression for 'conc' create a function and apply a
        # input.
        if moleculeDict.get('conc', ''):
            self.add_expression_to_pool(p, moleculeDict['conc'], 'conc')
        elif moleculeDict.get('n', ''):
            self.add_expression_to_pool(p, moleculeDict['conc'], 'n')
        else: pass

        self.molecules[molecule] = p
        return p

    def add_expression_to_pool(self, pool, expression, field = 'conc'):
        """generate conc of pool by a time dependent expression"""
        logger_.debug("Adding %s to pool %s" % (expression, pool))
        fieldFunc = moose.Function("%s/func_%s" % (pool.path, field))

        quit()

        

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

    def add_test(self, molecule):
        """To enable a  test, we need to attach a recorder """
        ltls = []
        for k in self.G.node[molecule].keys():
            if "test_" in k:
                ltl = te.LTL(k, self.G.node[molecule][k])
                ltls.append(ltl)
                self.add_recorder(molecule, ltl.field)
                self.nodes_with_tests.append(molecule)
                self.G.node[molecule]['ltls'] = ltls

    def add_recorder(self, molecule, field='conc'):
        # Add a table to molecule. 
        # TODO: Each molecule can have more than one table? 
        logger_.info("Adding a Table on : %s.%s" % (molecule, field))
        moose.Neutral('/tables')
        tablePath = '/tables/%s_%s' % (molecule, field)
        tab = moose.Table2(tablePath)
        elemPath = self.molecules[molecule]
        tab.connect('requestOut', elemPath, 'get' + field[0].upper() + field[1:])
        self.tables["%s.%s" % (molecule, field)] = tab
        self.G.node[molecule]['%s_table' % field] = tab
        return elemPath

    def run_test(self, time, node):
        n = self.G.node[node]
        te.execute_tests(time, n, node)

    def run(self, run_time=None, **kwargs):
        """
        Run model with given parameters.

        sim_time = simulation time
        outfile = File to save the results.
        """

        # get dt from chemviz file
        dt = float(self.G.graph['graph'].get('dt', 0.01))
        mu.info("Using dt=%s for all chemical process" % dt)
        for i in range(10, 16):
            moose.setClock(i, dt)
        moose.reinit()


        if 'sim_time' in self.G.graph['graph']:
            runtime = float(self.G.graph['graph']['sim_time'])
        else:
            runtime = float(run_time)

        logger_.info("Running MOOSE for %s" % runtime)
        moose.start(runtime)

        time = moose.Clock('/clock').currentTime
        if len(self.nodes_with_tests) > 0:
            [ self.run_test(time, n) for n in self.nodes_with_tests ]

        outfile = "%s.dat" % self.filename
        if kwargs.get('outfile', None) is not None:
            outfile = kwargs['outfile']

        mu.saveRecords(self.tables, outfile =  outfile )

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
