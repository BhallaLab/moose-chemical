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
from utils import expression as _expr
import operator as ops
import sys
from collections import defaultdict
import reaction
import tempfile
import matplotlib.pyplot as plt
import utils.typeclass as tc

import utils.typeclass as tc
import logging

logger_ = logging.getLogger('chemviz')
logger_.setLevel(logging.DEBUG)

def yacml_to_dot(text):
    """yacml_to_dot
    Convert YACML test to a dot.

    :param text: Text of YACML model.
    """
    text = text.replace('compartment', 'digraph')
    return text

def to_bool(arg):
    if arg.lower() in [ "0", "false", "no" ]:
        return False
    return True

def to_float(string):
    """Convert a given string to float """
    string = string.replace('"', '')
    return float(string)

def replace_in_expr(frm, to, expr):
    repExpr = re.compile(r'[\w]{0}[\w]'.format(frm))
    idents = repExpr.findall(expr)
    # protect these substrings.
    for i, p in enumerate(idents):
        expr = expr.replace(p, "##%s##" % i)

    # Now replace the given frm -> to
    expr = expr.replace(frm, to)
    # Put back the protected string.
    for i, p in enumerate(idents):
        expr = expr.replace('##%s##' % i, p)
    return expr

def get_path_of_node(moose_compt, name):
    return "%s/%s" % (moose_compt.path, name)

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
                try:
                    import pygraphviz 
                    self.G = nx.from_agraph(pygraphviz.AGraph(file=dotFile.name))
                except Exception as e:
                    pu.info("Failed with exception: %s" % e)
                    pu.fatal(["Failed to load graphviz file"
                        , "Tried pydot and pygraphviz" ]
                        )

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
        compt.volume = to_float(self.G.graph['graph']['volume'])

        # make sure the pools/buffpools are added to MOOSE before adding
        # reactions.

        logger_.info("============ Adding pools...")
        for node in self.G.nodes():
            nodeType = self.G.node[node]['type']
            if isinstance(nodeType, tc.Pool):
                self.add_molecules(node, compt)
            elif isinstance(nodeType, tc.Variable):
                self.add_variable(node, compt)
            else:
                pass
        # Now add expression to pools.
        logger_.info("============ Adding parameters/expressions to pools")
        for p in self.molecules:
            self.add_parameters_to_pool(p)

        logger_.info("============ Adding parameters/expressions to variables")
        for v in self.variables:
            self.add_parameters_to_var(v)

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

    def find_node(self, node_name):
        for n in self.G.nodes():
            if n == node_name:
                return n
        return None

    def add_molecules(self, node, compt):
        # check for the expression on molecule, it might depend on other
        # molecule. In that case, we must create those molecules first.
        logger_.info("Adding molecule: %s" % node)
        attr = self.G.node[node]
        if node in self.molecules:
            logger_.info("Molecule %s already exists" % node)
            return self.molecules[node]

        p = None
        if isinstance(attr['type'], tc.BufPool):
            p = self.add_bufpool(node, compt)
        elif isinstance(attr['type'], tc.Pool):
            p = self.add_pool(node, compt)
        else:
            pass

        assert p, "Must have created a moose.Pool/BufPool"
        self.molecules[node] = p
        if  attr.get('conc_init', False):
            p.concInit = float(attr['conc_init'])
            logger_.debug("|| set Conc_init to %s" % p.concInit)
        elif attr.get('N_init', False):
            p.nInit = float(attr['N_init'])
            logger_.debug("|| Set N_init to %s" % p.nInit)
        else:
            pass

    def add_variable(self, node, compt):
        """Adding a function undert compartment """
        logger_.info("Adding variable/function: %s" % node)
        attr = self.G.node[node]
        if node in self.functions:
            logger_.info("Function %s already exists" % node)
            return self.functions[node]

        f = moose.Function(get_path_of_node(compt, node))
        # NOTE: Always compute value of function. If derivative is given then
        # use increment/decrement messages else just set the value.
        f.mode = 1 
        logger_.debug("moose.Function mode: %s" % f.mode)
        self.variables[node] = f

    def replace_local_consts(self, expr, consts, const_dict):
        """replace all local constants in dictionary.
        """
        if len(consts) == 0:
            return expr
        elif len(const_dict) == 0:
            logger_.warn("These consts were not found in reaction: %s" % consts)
            return expr

        for c in sorted(consts, key=lambda x: len(x)):
            if c == 't':
                continue
            if c in const_dict:
                expr = replace_in_expr(c, const_dict[c], expr)
            else:
                logger_.debug("Constant %s not found in const" % c)
                continue
        return expr

    def replace_possible_subexpr(self, expr, constants, ids):
        """ If a id value can be converted to float, its a constant. Else its a
        subexpression
        """
        for i in ids:
            if i in constants:
                try: 
                    v = float(constants[i])
                except:
                    expr = expr.replace(i, constants[i])
        return expr

    def add_expr_to_function(self, expr, func, constants = {}, field = 'conc'):
        """Reformat a given expression and attach it to given function.

        Also connect y0, y1 etc to molecules or variables.
        """
        # Get the replaceable identifier in given expression.
        ids = _expr.get_ids(expr)
        logger_.debug("IDs: %s" % ",".join(ids))

        # Find a subexpression, insert into expression. If expression changes,
        # call this function again.
        new_expr = _expr.replace_possible_subexpr(expr, constants, ids)
        if new_expr != expr:
            # and serach of ids again.
            return self.add_expr_to_function(new_expr, func, constants, field)

        # If id is found in molecules, its a moose.Pool/BufPool, if it is a
        # variable, its moose.Function else it is a constant which must be
        # replaced by a value.  
        ## NOTE: Or it is 't'
        pools = set()
        variables = set()
        localConstants = []
        transDict = {}

        for i in ids:
            if self.molecules.get(i, None) is not None:
                pools.add(i)
            elif self.variables.get(i, None) is not None:
                variables.add(i)
            else: 
                # If this is a numerical value, put it in constants else replace
                localConstants.append(i)

        for i, p in enumerate(pools):
            pp, y = self.molecules[p], "y%s" % i
            expr = replace_in_expr(p, y, expr)
            transDict[y] = pp

        for i, var in enumerate(variables):
            v, y = self.variables[var], "y%s" % (len(pools)+i)
            expr = replace_in_expr(v.name, y, expr)
            transDict[y] = v

        expr = self.replace_local_consts(expr, localConstants, constants)
        logger_.info("Adding expression after replacement: %s" % expr)
        func.expr = expr

        # After replacing variables with appropriate yi's, connect
        # them to appropriate MOOSE elements.: GO in ordered sequences.
        for k in sorted(transDict.keys()):
            elem = transDict[k]
            if isinstance(elem, moose.Pool) or isinstance(elem, moose.BufPool):
                f = 'get' + field[0].upper() + field[1:]
            elif isinstance(elem, moose.Function):
                f = 'getValue'
            else:
                raise UserWarning("Can't find the type of source elem %" % elem)
            logger_.debug("|READ| %s.%s <-- %s.%s" % (func.path, k, transDict[k].path, f))
            moose.connect(func, 'requestOut', transDict[k], f)


    def add_forward_rate_expr(self, reac, expr, constants):
        """Add an expression for forward rate constant"""
        logger_.debug("| Forward rate expression: %s" % expr)
        # FIXME: If any function is created under ksolve.path, then it causes
        # seg fault. Reported on github=moose-core.
        #funcPath = '%s/%s_forward_expr_f' % (self.funcPath, reac.name)
        funcPath = '%s/%s_forward_expr_f' % (reac.path, reac.name)
        forwardExprFunc = moose.Function(funcPath)
        self.add_expr_to_function(expr, forwardExprFunc, constants=constants)
        forwardExprFunc.mode = 1
        logger_.debug("||WRITE| %s --> %s.%s" % (forwardExprFunc, reac, 'setKf'))
        moose.connect(forwardExprFunc, 'valueOut', reac, 'setKf') 

    def add_backward_rate_expr(self, reac, expr, constants):
        """Add an expression for backward rate constant
        """
        logger_.debug("| Backward rate expression: %s" % expr)
        funcPath = '%s/backward_expr_f' % reac.path
        backwardFunction = moose.Function(funcPath)
        self.add_expr_to_function(expr, backwardFunction, constants=constants)
        logger_.debug("||WRITE| %s --> %s.%s" % (backwardFunction, reac, 'setKb'))
        moose.connect(backwardFunction, 'valueOut', reac, 'setKb') 

    def add_reaction_attr(self, reac, attr):
        """Add attributes to reaction.
        """
        kf = attr['kf']
        kb = attr['kb']
        try:
            reac.Kf = float(kf)
        except Exception as e:
            self.add_forward_rate_expr(reac, kf, constants = attr)
        try:
            reac.Kb = float(kb)
        except Exception as e:
            self.add_backward_rate_expr(reac, kb, constants = attr)

    def add_reaction(self, node, compt):
        """Add a reaction node to MOOSE"""
        attr = self.G.node[node]
        attr['shape'] = 'rect'
        logger_.info("| Adding a reaction: %s" % node)
        logger_.debug("|| With attribs %s:" % attr)
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
        """Add a moose.Pool for a given molecule. DO NOT ADD parameters to pool
        here since expression might depend on other variables and pool which are
        not yet added. This is like Forward Declaration.
        """

        logger_.info("Adding molecule %s as moose.Pool" % molecule)
        moleculeDict = self.G.node[molecule]
        logger_.debug("|- %s" % moleculeDict)
        poolPath = '{}/{}'.format(compt.path, molecule)
        p = moose.Pool(poolPath)
        return p

    def add_bufpool(self, molecule, compt):
        """Add a moose.BufPool to moose for a given molecule """
        logger_.info("Adding molecule %s as moose.BufPool" % molecule)
        poolPath = get_path_of_node(compt, molecule)
        moleculeDict = self.G.node[molecule]
        logger_.debug("|- %s" % moleculeDict)
        p = moose.BufPool(poolPath)
        return p

    def add_parameters_to_var(self, variable):
        mooseFunc = self.variables[variable]
        assert mooseFunc
        attribs = self.G.node[variable]
        if attribs.get('plot', None): 
            self.add_recorder(mooseFunc, 'value')
        funcExpr = attribs.get(variable, attribs.get('%s' % variable))
        assert funcExpr, "No expression {0}".format(variable)
        self.add_expr_to_function(funcExpr, mooseFunc, constants = attribs)

    def add_parameters_to_pool(self, pool):
        """Add expression to Pool/BufPool. Initial concentration/number has
        already be assigned by add_molecules function.
        """
        moose_pool = self.molecules[pool]
        attribs = self.G.node[pool]
        pool = attribs['type']
        if pool.concOrN in ['conc', 'n']:
            self.add_pool_expression(moose_pool, attribs)
            if attribs.get('plot', None):
                assert moose_pool, "moose_pool shouldn't be NULL"
                if attribs['plot'] in [ 'conc', 'N' ]:
                    self.add_recorder(moose_pool, attribs['plot'])
                else:
                    logger_.warn("Supported conc/N, not %s." % attribs['plot'])
                    logger_.info("Using default on pool")
                    self.add_recorder(moose_pool, pool.concOrN)
        else:
            pu.fatal("Neither conc or n expression on pool %s" % pool)

    def add_pool_expression(self, moose_pool, attribs):
        """generate conc of moose_pool by a time dependent expression"""

        typeObj = attribs['type']
        field = typeObj.concOrN
        expression = None
        if field == 'conc':
            expression = typeObj.conc
            try: 
                moose_pool.concInit = float(expression)
                moose_pool.conc = float(expression)
                logger_.debug("| Assigned conc=%s to pool %s" % (moose_pool.conc, moose_pool))
                return moose_pool
            except:
                pass
        elif field == 'n':
            expression = typeObj.n
            try:
                moose_pool.nInit = float(expression)
                logger_.debug("| Assigned n=%s to pool %s" % (moose_pool.n, moose_pool))
                moose_pool.n = int(expression)
                return moose_pool
            except:
                pass

        assert expression, "Pool must some expression %s" % attribs
        logger_.info("Adding expr %s to moose_pool %s" % (expression, moose_pool))
        ## FIXME: issue #32 on moose-core. Function must not be created under
        ## stoich.path.
        func = moose.Function("%s/func_%s" % (moose_pool.path, field))

        ## FIXME: This is safe but does not work with stochastic solver.
        #func = moose.Function("%s/fun_%s_%s" % (self.funcPath, moose_pool.name, field))
        self.add_expr_to_function(expression, func
                , field = field
                , constants = attribs
                )

        # FIXME: issue #3
        #moose_pool = moose.BufPool(moose_pool)
        #self.molecules[moose_pool.name] = moose_pool

        outfield = 'set' + field[0].upper()+field[1:]
        if not typeObj.rate:
            func.mode = 1
            source = 'valueOut'
        else:
            func.mode = 3
            source = 'rateOut'
        logger_.debug("|WRITE| %s.%s --> %s.%s" % (func.path, source
            , moose_pool.path, outfield)
            )
        logger_.debug("||| Func mode is: %s" % func.mode)
        moose.connect(func, source,  moose_pool, outfield)

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
        # Add a table to element. 
        # TODO: Each molecule can have more than one table? 
        elem = moose_elem.name
        logger_.info("| Adding a Table on : %s.%s" % (elem, field))
        moose.Neutral('/tables')
        tablePath = '/tables/%s_%s' % (elem, field)
        tab = moose.Table2(tablePath)
        moose.connect(tab, 'requestOut', moose_elem, 'get' + field[0].upper() + field[1:])
        self.tables["%s.%s" % (elem, field)] = tab
        try:
            self.G.node[elem]['%s_table' % field] = tab
        except:
            logger_.warn("Could not store table on graph node %s" % elem)
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
