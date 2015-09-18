"""chemviz.py

    load YACML.
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
import moose.print_utils as pu
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
import utils.typeclass as tc

import utils.typeclass as tc
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

def to_bool(arg):
    if arg.lower() in [ "0", "f", "false", "no", "n" ]:
        return False
    return True

class DotModel():
    '''
    Parse graphviz file and populate a chemical model in MOOSE.
    '''

    def __init__(self, modelFile):
        self.filename = modelFile
        self.G = nx.MultiDiGraph()
        self.molecules = {}
        self.npools = 0
        self.nbufpool = 0
        self.nreac = 0
        self.enzymes = {}
        self.reactions = {}
        self.kinetics = {}
        self.functions = {}
        self.poolPath = None
        self.modelPath = '/model'
        self.funcPath = '/model/functions'
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
        for path in [self.modelPath, self.funcPath]:
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

    def initialize_graph(self):
        """Initialize a given graph 
        """
        for n in self.G.nodes():
            attr = self.G.node[n]
            self.G.node[n]['do_test'] = "false"
            for k in attr.keys():
                if "test" in k: 
                    self.G.node[n]['do_test'] = "true"
            self.attach_type(n)

        logger_.info("Reactions = {0}, Pools(buffered) = {1}({2})".format(
            self.nreac , self.npools , self.nbufpool))

    def attach_type(self, n):
        """This function attach types to node 'n' of graph"""
        attr = self.G.node[n]
        ntype = tc.determine_type(n, self.G)
        logger_.info("Type of node %s is %s" % (n, ntype))
        self.G.node[n]['type'] = ntype
        
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
                pu.error(["Failed to load YACML file." 
                    , "Error was %s" % e
                    ])

        self.G = nx.MultiDiGraph(self.G)
        assert self.G.number_of_nodes() > 0, "Zero molecules"
        self.initialize_graph()


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

        # make sure the pools/buffpools are added to MOOSE before adding
        # reactions.
        for node in self.G.nodes():
            attr = self.G.node[node]
            if isinstance(attr['type'], tc.BufPool):
                self.molecules[node] = self.add_bufpool(node, compt)
            elif isinstance(attr['type'], tc.Pool):
                self.molecules[node] = self.add_pool(node, compt)
            else:
                pass

        for node in self.G.nodes():
            attr = self.G.node[node]
            if isinstance(attr['type'], tc.EnzymaticReaction):
                self.reactions[node] = self.add_enzymatic_reaction(node, compt)
            elif isinstance(attr['type'], tc.Reaction):
                self.reactions[node] = self.add_reaction(node, compt)
            else:
                pass

        # NOTICE: Solvers are always set in the end.
        self.setup_solvers()

        # Dump the edited graph into a temp file.
        outfile = '%s.dot' % self.filename
        logger_.debug("Writing network to : %s" % outfile)
        nx.write_dot(self.G, outfile)


    def add_expr_to_function(self, expr, func, field = 'conc'):
        """Reformat a given expression 

        Attach a expression to given function.

        Also connect y0, y1 etc to molecules.
        """
        transDict = {}
        astExpr = ast.parse(expr)
        i = 0

        # Replace all variables with MOOSE elements.
        for node in ast.walk(astExpr):
            if type(node) == ast.Name:
                if self.molecules.get(node.id, None) is not None:
                    key, val = 'y%s' %i, self.molecules[node.id]
                    expr = expr.replace(node.id, key)
                    transDict[key] = val
                    i += 1

        logger_.debug("Adding expression: %s" % expr)
        func.expr = expr

        # After replacing variables with appropriate yi's, connect
        # them to appropriate MOOSE elements.
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
        pu.info(["Adding a reaction: %s" % node, "With attribs %s:" % attr])
        reac = moose.Reac('%s/%s' % (compt.path, node))
        self.G.node[node]['reaction'] = reac
        self.add_reaction_attr(reac, attr)
        for sub, tgt in self.G.in_edges(node):
            logger_.debug("Adding sub to reac: %s" % sub)
            moose.connect(reac, 'sub', self.molecules[sub], 'reac')
        for sub, tgt in self.G.out_edges(node):
            logger_.debug("Adding prd to reac: %s" % tgt)
            moose.connect(reac, 'prd', self.molecules[tgt], 'reac')
        return reac.path

    def add_enzymatic_reaction(self, node, compt):
        """Add an enzymatic reaction """
        attr = self.G.node[node]
        pu.info(["Adding an enz-reaction: %s" % node, "With attribs %s:" % attr])
        enz = self.molecules[attr['enzyme']]
        # Use this enzyme to create an enz-complex
        enzPath = '{0}/enz'.format(enz.path)

        mooseEnz = moose.Enz(enzPath)

        mooseEnz.Km = float(attr['km'])
        mooseEnz.kcat = float(attr['kcat'])

        moose.connect(mooseEnz, 'enz', enz, 'reac')

        mooseEnzCplx = moose.Pool('%s/cplx' % enzPath)
        moose.connect(mooseEnz, 'cplx', mooseEnzCplx, 'reac')

        # Attach substrate and product to enzymatic reaction.
        for sub, tgt in self.G.in_edges(node):
            logger_.debug("Adding sub to enz-reac: %s" % sub)
            moose.connect(mooseEnz, 'sub', self.molecules[sub], 'reac')
        for sub, tgt in self.G.out_edges(node):
            logger_.debug("Adding prd to enz-reac: %s" % tgt)
            moose.connect(mooseEnz, 'prd', self.molecules[tgt], 'reac')

    def setup_solvers(self):
        """setup_solvers Add solvers after model is loaded. 

        One compartment can only have one solver, so its a property of
        graph/subgraph.

        """
        solver = self.G.graph['graph'].get('solver', 'ksolve')
        self.setup_solver(solver.lower(), self.__cur_compt__)


    def setup_solver(self, solver, compt, **kwargs):
        """setup_solver. Use a solver for given reaction. Solvers must be set in
        the end.

        :param reac: moose.Reaction element.
        :param solver: Type of solver i.e. ksolve/gsolve, string.
        """
        pu.info("Adding a solver %s to compartment %s" % (solver, compt.path))
        s = None
        if solver == "ksolve":
            s = moose.Ksolve('%s/ksolve' % compt.path)
        elif solver == 'gsolve':
            s = moose.Gsolve('%s/gsolve' % compt.path)
        else:
            msg = "Unknown solver: %s. Using ksolve." % solver
            pu.warn(msg)

        stoich = moose.Stoich('%s/stoich' % compt.path)
        # NOTE: must be set before compartment or path.
        assert s
        stoich.ksolve = s
        stoich.compartment = compt
        stoich.path = '%s/##' % compt.path

    def add_pool(self, molecule, compt):
        """Add a moose.Pool for a given molecule """

        pu.info("Adding molecule %s as moose.Pool" % molecule)
        moleculeDict = self.G.node[molecule]
        logger_.debug("|- %s" % moleculeDict)
        poolPath = '{}/{}'.format(compt.path, molecule)
        p = moose.Pool(poolPath)
        pool = self.G.node[molecule]['type']
        isPlot = to_bool(moleculeDict.get('plot', 'false'))
        self.add_parameters_to_pool(p, pool, plot=isPlot)
        return p

    def add_bufpool(self, molecule, compt):
        """Add a moose.BufPool to moose for a given molecule """
        pu.info("Adding molecule %s as moose.BufPool" % molecule)
        poolPath = '{}/{}'.format(compt.path, molecule)
        moleculeDict = self.G.node[molecule]
        logger_.debug("|- %s" % moleculeDict)
        p = moose.BufPool(poolPath)
        bufpool = self.G.node[molecule]['type']
        isPlot = to_bool(moleculeDict.get('plot', 'false'))
        self.add_parameters_to_pool(p, bufpool, isPlot) 
        return p

    def add_parameters_to_pool(self, moose_pool, pool, plot = False):
        if pool.concOrN == 'conc':
            if plot:
                self.add_recorder(moose_pool, 'conc')
            if type(pool.conc) == float:
                logger_.debug("Setting %s.concInit to %s" % (moose_pool, pool.conc))
                moose_pool.concInit = pool.conc
            elif type(pool.conc) == str:
                self.add_pool_expression(moose_pool, pool.conc, 'conc')
            else:
                pu.fatal([ "Unsupported conc expression on pool %s" % molecule
                    , pool.conc
                    ])
        elif pool.concOrN == 'n':
            if plot:
                self.add_recorder(moose_pool, 'n')
            if type(pool.n) == int:
                logger_.debug("Setting %s.nInit to %s" % (moose_pool, pool.n))
                moose_pool.nInit = pool.n
            elif type(pool.n) ==  str:
                self.add_pool_expression(moose_pool, pool.n, 'n')
            else:
                pu.fatal([ "Unsupported n expression on pool %s" % molecule
                    , pool.n ])
        else:
            pu.fatal("Neither conc or n expression on pool %s" % molecule)
        self.molecules[moose_pool.name] = moose_pool

    def add_pool_expression(self, moose_pool, expression, field = 'conc'):
        """generate conc of moose_pool by a time dependent expression"""
        logger_.info("Adding %s to moose_pool %s" % (expression, moose_pool))
        
        ## fixme: issue #32 on moose-core. Function must not be created under
        ## stoich.path.
        #func = moose.Function("%s/func_%s" % (moose_pool.path, field))

        ## This is safe.
        func = moose.Function("%s/func_%s" % (self.funcPath, field))
        self.add_expr_to_function(expression, func, field)
        func.mode = 1
        moose.connect(func, 'valueOut', moose_pool, 'set'+field[0].upper()+field[1:])

    ##def add_enzyme(self, molecule, compt):
    ##    """Add an enzyme """
    ##    enzPath = '{}/{}'.format(compt.path, molecule)
    ##    enz =  moose.Enz(enzPath)
    ##    e = self.G.node[molecule]['type']
    ##    if type(e.km) == float:
    ##        enz.Km = e.km
    ##    else:
    ##        pu.dump("TODO", "Support string expression on Km")
    ##    if type(e.kcat) == float:
    ##        enz.kcat = e.kcat
    ##    else:
    ##        pu.dump("TODO", "Support string expression on kcat")
    ##    return enz

    def add_test(self, molecule):
        """To enable a  test, we need to attach a recorder """
        ltls = []
        for k in self.G.node[molecule].keys():
            if "test_" in k:
                ltl = te.LTL(k, self.G.node[molecule][k])
                ltls.append(ltl)
                self.add_recorder(self.molecules[molecule], ltl.field)
                self.nodes_with_tests.append(molecule)
                self.G.node[molecule]['ltls'] = ltls

    def add_recorder(self, moose_elem, field='conc'):
        # Add a table to molecule. 
        # TODO: Each molecule can have more than one table? 
        molecule = moose_elem.name
        logger_.info("Adding a Table on : %s.%s" % (molecule, field))
        moose.Neutral('/tables')
        tablePath = '/tables/%s_%s' % (molecule, field)
        tab = moose.Table2(tablePath)
        tab.connect('requestOut', moose_elem, 'get' + field[0].upper() + field[1:])
        self.tables["%s.%s" % (molecule, field)] = tab
        self.G.node[molecule]['%s_table' % field] = tab
        return moose_elem.path

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
        pu.info("Using dt=%s for all chemical process" % dt)
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
