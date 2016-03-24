"""yacml2moose.py

Load YACML model into MOOSE simulator.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2016, Dilawar Singh"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


import math
import networkx.drawing.nx_agraph as nxAG
import networkx as nx
import moose
import moose.print_utils as pu
import moose.utils as mu
import ast
import re
from utils import test_expr as te
from utils import expression as _expr
import notify as warn
import config
import operator as ops
import sys
from collections import defaultdict
import tempfile
import matplotlib.pyplot as plt
from utils import typeclass as tc
from utils.helper import *
logger_ = config.logger_

def replace_in_expr(frm, to, expr):
    repExpr = re.compile(r'[\w]{0}[\w]'.format(frm))
    idents = repExpr.findall(expr)
    # protect these substrings.
    for i, p in enumerate(idents):
        expr = expr.replace(p, "##%s##" % i)
    expr = expr.replace('"', '')

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

    def __init__(self, G, section = 0, **kwargs):
        """__init__

        :param G: networkx graph representing model
        :param prefix: Prefix for each entitiy inside this graph. Very useful if
        you want to load this model more than 1 times in the very same
        compartment. Different prefix value in each call make sure that entities
        are not replaced.
        :param **kwargs:
            optional.
        """
        self.G = G
        self.options = kwargs
        self.globals_ = self.G.graph['graph']
        self.filename = self.globals_['filename']
        self.molecules = {}
        self.npools = 0
        self.nbufpool = 0
        self.nreac = 0
        self.enzymes = {}
        self.reactions = {}
        self.kinetics = {}
        self.functions = {}
        self.poolPath = None
        self.rootPath = '/yacml'
        moose.Neutral( self.rootPath )
        self.comptPath = '%s/%s' % (self.rootPath, self.G.name)
        self.funcPath = '%s/functions' % self.comptPath
        self.variables = {}
        self.tables = {}
        self.nodes_with_tests = []
        self.compartments = {}
        self.solver = None
        self.compartment = None
        self.__cwd__ = ""
        self.__cur_compt__ = None
        self.__prefix__ = '%s' % section
        # Finally load the model
        self.load()

    def prefixed_path( self, identifier ):
        """prefixed Prefix the given indentifier with compartment prefix

        :param identifier:
        """
        return "%s/%s/%s" % (self.comptPath,  self.__prefix__, identifier)


    def create_compartment( self ):
        """Create a compartment with given geomtry. If none given, use
        cylinderical
        """
        if moose.exists( self.comptPath ):
            logger_.warn(' Compartment (%s) already exist' % self.comptPath )
            return moose.Neutral( self.comptPath )
        if self.globals_.get('geometry', 'cube').lower() == 'cube':
            logger_.info("Creating cubical compartment")
            curCompt =  moose.CubeMesh( self.comptPath )
            curCompt.volume = eval(self.globals_['volume'])
        else:
            logger_.info("Creating cylinderical compartment")
            curCompt = moose.CylMesh( self.comptPath )
            curCompt.r0 = curCompt.r1 = eval(self.globals_['radius'])

        if 'length' in self.globals_:
            curCompt.x0 = 0.0
            curCompt.x1 = eval(self.globals_['length'])
        elif 'x0' in self.globals_ and 'x1' in globals_:
            curCompt.x0 = eval(self.globals_['x0'])
            curCompt.x1 = eval(self.globals_['x1'])
        else:
            logger_.fatal( 'Failed to find either "length" or "r0" and "r1"'
                    ' in your model. '
                        )
        # Diffusion length can only be set after length is set
        # NOTE: Use it if only diffusion solver is used.

        return curCompt


    def init_moose(self, compt):
        """Initialize paths in MOOSE"""

        curCompt = self.create_compartment( )
        moose.Neutral( '%s/%s' % (curCompt.path, self.__prefix__ ) )
        for path in [self.funcPath]:
            moose.Neutral(path)
        self.compartments[self.G.name] = curCompt
        self.poolPath = curCompt.path
        self.__cwd__ = curCompt.path
        self.__cur_compt__ = curCompt
        self.compartment = curCompt

    def initialize_graph(self):
        """Initialize a given graph 
        """
        for n in self.G.nodes():
            self.G.node[n]['label'] = n 
            self.G.node[n]['path'] = self.prefixed_path( n )

        for n in self.G.nodes():
            attr = self.G.node[n]
            self.G.node[n]['do_test'] = "false"
            for k in attr.keys():
                if "test" in k: 
                    self.G.node[n]['do_test'] = "true"
            self.attach_type(n)

    def attach_type(self, n):
        """This function attach types to node 'n' of graph"""
        attr = self.G.node[n]
        ntype = tc.determine_type(n, self.G)
        logger_.info("Type of node %s is %s" % (n, ntype))
        self.G.node[n]['type'] = ntype
        
    def checkNode(self, n):
        return True

    def checkEdge(self, src, tgt):
        return True

    def load(self, compt = None):
        '''Load given model into MOOSE'''

        self.initialize_graph( )
        self.init_moose(compt)
        compt = self.__cur_compt__ 

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

        logger_.info("============ Adding reactions")
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
        nxAG.write_dot(self.G, outfile)

    def find_node(self, node_name):
        for n in self.G.nodes():
            if n == node_name:
                return n
        return None

    def add_molecules(self, node, compt):
        # check for the expression on molecule, it might depend on other
        # molecule. In that case, we must create those molecules first.
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
        if  attr.get('conc', False):
            try:
                p.concInit = float(eval(attr['conc']))
                logger_.debug("|| set concInit to %s" % p.concInit)
            except Exception as e:
                pass
        elif attr.get('N', False):
            try:
                p.nInit = float(eval(attr['N']))
                logger_.debug("|| Set nInit to %s" % p.nInit)
            except Exception as e:
                pass
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

    def replace_constants(self, expr, consts, const_dict):
        """
        replace all local/global constants in dictionary.
        """
        if len(consts) == 0:
            return expr
        elif len(const_dict) == 0:
            logger_.warn("These consts were not found in reaction: %s" % consts)
            return expr

        # The list of  constants, wheather local or global is generated
        # beforehand. It is neccessay to sort it and replace the smaller
        # constant first. Now I forgot why I was doing this, but it is working
        # and bug free.
        for c in sorted(consts, key=lambda x: len(x)):
            # t is a special variable. It is connected to internal clock
            # automatically.
            if c == 't':
                continue
            if c in const_dict:
                logger_.debug("Local constant : %s" % c)
                expr = replace_in_expr(c, const_dict[c], expr)
            elif c in self.G.graph['graph']:
                logger_.debug("Found in globals: %s" % c)
                expr = replace_in_expr(c, self.G.graph['graph'][c], expr)
            else:
                logger_.debug("Constant %s not found in const" % c)
                continue
        return expr

    def add_expr_to_function(self, expr, func, constants = {}, field = 'n'):
        """Reformat a given expression and attach it to given function.

        Also connect x0, x1 etc to molecules or variables.
        """

        # Get the replaceable identifier in given expression.
        ids = _expr.get_ids(expr)
        logger_.debug("[FUNC| IDs: %s" % ",".join(ids))

        # If id is found in molecules, its a moose.Pool/BufPool, if it is a
        # variable, its moose.Function else it is a constant which must be
        # replaced by a value.  
        ## NOTE: Or it is 't'
        pools = set()
        variables = set()
        transDict = {}

        for i in ids:
            if self.molecules.get(i, None) is not None:
                pools.add(i)
            elif self.variables.get(i, None) is not None:
                variables.add(i)
            else: 
                pass

        for i, p in enumerate(pools):
            pp, y = self.molecules[p], "x%s" % i
            expr = replace_in_expr(p, y, expr)
            transDict[y] = pp

        # These variables are to be replaced by x0, x1 etc. Variables takes
        # input from either moose.Function or moose.Pools.
        for i, var in enumerate(variables):
            v, y = self.variables[var], "x%s" % (len(pools)+i)
            expr = replace_in_expr(v.name, y, expr)
            transDict[y] = v

        logger_.info("Adding expression after replacement: %s" % expr)
        func.expr = expr.replace('"', '')

        # After replacing variables with appropriate xi's, connect
        # them to appropriate MOOSE elements.: GO in ordered sequences.
        func.x.num = len(transDict)
        for i, k in enumerate(sorted(transDict.keys())):
            elem = transDict[k]
            if isinstance(elem, moose.Pool) or isinstance(elem, moose.BufPool):
                f = field + 'Out'
            elif isinstance(elem, moose.Function):
                f = 'valueOut'
            else:
                raise UserWarning("Can't find the type of source elem %" % elem)
            logger_.debug("|READ| %s.%s <-- %s.%s" % (func.path, k, transDict[k].path, f))
            try:
                moose.connect(transDict[k], f, func.x[i], 'input')
            except NameError as e:
                print(warn.issue_72( ))
                quit()


    def add_rate_expr(self, reac, field, expr, constants):
        """Add an expression for forward/backward rate"""
        # If expr can be converted to float, simply set the expression to float.
        # Otherwise, compute the value using moose.Function and set the value.
        # NOTE: When using function, one needs to use numKf/numKb instead of
        # Kf/Kb.
        try:
            value = eval(str(expr))
            if field == 'kf': reac.Kf = value
            elif field == 'kb': reac.Kb = value
            elif field == 'numKf': reac.numKf = value
            elif field == 'numKb': reac.numKb = value
            else:
                logger_.warn("Unknown field %s for reaction" % field)
                logger_.warn(' Ignored!' )
            logger_.debug("|=  Rate expression for %s is %f" % (field, value))
            return True
        except Exception as e:
            logger_.debug("|REACTION| could not convert to float: %s" % e)
            funcPath = '%s/func_%s' % (reac.path, field)
            rateFunc = moose.Function(funcPath)
            self.add_expr_to_function(expr, rateFunc, constants=constants)
            rateFunc.mode = 1
            # NOTE: setting up Kf is not encouraged because this leads to
            # scaling effects in small volumes.
            setField = 'set' + field[0].upper() + field[1:]
            logger_.debug("||WRITE| %s.valueOut --> %s.%s" % (rateFunc, reac, field))
            moose.connect(rateFunc, 'valueOut', reac, setField) 
            return True

    def add_reaction_attr(self, reac, attr):
        """Add attributes to reaction.
        """
        if 'numKf' in attr:
            self.add_rate_expr( reac, 'numKf', attr['numKf'], attr )
        elif 'kf' in attr:
            self.add_rate_expr( reac, 'kf', attr['kf'], attr)
        else: 
            logger_.warn('Expecting kf or numKf in paramters. Check your reaction!')

        if 'numKb' in attr:
            self.add_rate_expr( reac, 'numKb', attr['numKb'], attr)
        elif 'kb' in attr:
            self.add_rate_expr( reac, 'kb', attr['kb'], attr )
        else:
            logger_.warn('Expecting kb or numKb in paramters. Check your reaction!')

    def add_reaction(self, node, compt):
        """Add a reaction node to MOOSE"""
        attr = self.G.node[node]
        attr['shape'] = 'rect'
        subs, prds = [], []

        logger_.debug("|REACTION| With attribs %s:" % attr)
        reac = moose.Reac( self.G.node[node]['path'] )
        self.G.node[node]['reaction'] = reac


        for sub, tgt in self.G.in_edges(node):
            logger_.debug("|REACTION| Adding sub to reac: %s" % sub)
            moose.connect(reac, 'sub', self.molecules[sub], 'reac')
            subs.append( sub )
        for sub, tgt in self.G.out_edges(node):
            logger_.debug("|REACTION| Adding prd to reac: %s" % tgt)
            moose.connect(reac, 'prd', self.molecules[tgt], 'reac')
            prds.append( tgt )

        # NOTE: Potentially a bug. The reaction attributes must be added after
        # subs and prds are added.
        self.add_reaction_attr(reac, attr)

        logger_.info("Added reaction {name}: {subs} <== {kb}, {kf} ==> {prds}".format( 
            name = node, subs=",".join(subs), prds=",".join( prds ) 
            , kf = str(reac.numKf), kb = str(reac.numKb)
            )
            )
        if not (subs and prds ):
            mu.warn( "CAREFUL! This reaction has missing substrates/products" )

        return reac.path

    def add_enzymatic_reaction(self, node, compt):
        """Add an enzymatic reaction """
        attr = self.G.node[node]
        pu.info(["Adding an enz-reaction: %s" % node, "With attribs %s:" % attr])
        enz = self.molecules[attr['enzyme']]
        # Use this enzyme to create an enz-complex
        enzPath = '{0}/enz'.format(enz.path)

        mooseEnz = moose.Enz(enzPath)

        mooseEnz.Km = eval(attr['km'])
        mooseEnz.kcat = eval(attr['kcat'])

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

        solver = self.G.graph['graph'].get('solver')
        if solver:
            self.setup_solver(solver.lower(), self.__cur_compt__)
        else:
            mu.warn( [ 
                "You did not specify a solver!"
                , "May be you want to set it up later. Otherwise I'll use default"
                ] )
        return None


    def setup_solver(self, solver, compt, **kwargs):
        """setup_solver. Use a solver for given reaction. Solvers must be set in
        the end.

        :param reac: moose.Reaction element.
        :param solver: Type of solver i.e. ksolve/gsolve, string.

        """

        # If solver already exists in this compartment, do not add another
        # solver. This is useful when more than one sections are added to
        # compartment.
        solverPath = '%s/stoich' % compt.path
        if moose.exists( solverPath ):
            pu.warn("I've already added a solver on comparment %s" % compt.name)
            pu.warn("I won't add another solver. This usually causes segfaults")
            return moose.Stoich( solverPath )

        pu.info("Adding a solver %s to compartment %s" % (solver, compt.path))
        s = None
        if solver == "deterministic":
            pu.info('[INFO] Using deterministic solver')
            s = moose.Ksolve('%s/ksolve' % compt.path)
        elif solver == 'stochastic':
            pu.info('Using stochastic solver')
            s = moose.Gsolve('%s/gsolve' % compt.path)
            pu.info("Setting 'useClockedUpdate = True'; Honors function events.")
            s.useClockedUpdate = True
        else:
            msg = "Unknown solver: %s. Using 'deterministic' solver." % solver
            msg += "\n Choices: 'stochastic' and 'deterministic' (default)'"
            pu.warn(msg)
            s = moose.Ksolve('%s/ksolve' % compt.path)

        # If diffusion is enabled, then setup a solver to handle diffusion
        if 'enable_diffusion' in self.globals_:
            pu.info( 'Setting up solver to handle diffusion' )
            dsolvePath = '%s/dsolve' % compt.path
            if moose.exists( dsolvePath ):
                mu.warn( 'Already exists %s. Doing nothing. ' % dsolvePath )
            else:
                dsolve = moose.Dsolve( '%s/dsolve' % compt.path )

        stoich = moose.Stoich('%s/stoich' % compt.path)
        # NOTE: must be set before compartment or path.
        stoich.compartment = compt
        stoich.ksolve = s
        if 'enable_diffusion' in self.globals_:
            stoich.dsolve = dsolve

        stoich.path = '%s/##' % compt.path
        self.solver = stoich
        return stoich

    def add_pool(self, molecule, compt):
        """Add a moose.Pool for a given molecule. DO NOT ADD parameters to pool
        here since expression might depend on other variables and pool which are
        not yet added. This is like Forward Declaration.
        """

        moleculeDict = self.G.node[molecule]
        logger_.debug("|- %s" % moleculeDict)
        p = moose.Pool( self.G.node[molecule]['path'] )
        p.diffConst = eval( 
                self.G.node[molecule].get('diffusion_constant', '0.0')
                )
        logger_.info("Added  %s (diffusion_constant=%s) as moose.Pool" % (
            molecule, p.diffConst ))
        return p

    def add_bufpool(self, molecule, compt):
        """Add a moose.BufPool to moose for a given molecule """
        poolPath = self.G.node[molecule]['path'] #get_path_of_node(compt, molecule)
        moleculeDict = self.G.node[molecule]
        logger_.debug("|- %s" % moleculeDict)
        p = moose.BufPool(poolPath)
        p.diffConst = eval( 
                self.G.node[molecule].get('diffusion_constant', '0.0')
                )
        logger_.info("Added  %s (diffusion_constant=%s) as moose.BufPool" % (
            molecule, p.diffConst ))
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
            pu.fatal("Neither conc or N expression on pool %s" % pool)

    def add_pool_expression(self, moose_pool, attribs):
        """generate conc of moose_pool by a time dependent expression"""
        typeObj = attribs['type']
        field = typeObj.concOrN
        expression = None
        if field == 'conc':
            expression = str(typeObj.conc)
            assert expression
            try: 
                moose_pool.concInit = eval(expression)
                moose_pool.conc = eval(expression)
                logger_.debug("| Assigned conc=%s to pool %s" % (moose_pool.conc, moose_pool))
                return moose_pool
            except Exception as e:
                logger_.debug('|POOL| set conc: %s' % e)
                pass
        elif field == 'n':
            expression = str(typeObj.n)
            try:
                moose_pool.nInit = eval(str(expression))
                logger_.debug("| Assigned n=%s to pool %s" % (moose_pool.n, moose_pool))
                moose_pool.n = eval(str(expression))
                return moose_pool
            except Exception as e:
                logger_.debug("|POOL| %s" % e)
                pass

        assert expression, \
                "Pool %s must have expression for conc/n in %s" % (moose_pool, attribs)
        logger_.info("Adding expr %s to moose_pool %s" % (expression, moose_pool))
        ## FIXME: issue #32 on moose-core. Function must not be created under
        ## stoich.path.
        moose.Neutral("%s/%s" % ( moose_pool.path, field ))
        func = moose.Function("%s/%s_func" % (moose_pool.path, field))
        self.add_expr_to_function(expression, func, attribs, field)

        outfield = 'set' + field[0].upper()+field[1:]
        if not typeObj.rate:
            func.mode = 1
            source = 'valueOut'
        else:
            func.mode = 3
            source = 'rateOut'
        logger_.debug("|FUNC| Func mode is: %s" % func.mode)
        logger_.debug("|FUNC|WRITE| {0}.{1} --> {2}.{3}".format(
            func.path, source , moose_pool.path, outfield)
            )
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
        logger_.debug("Adding a Table on : %s.%s" % (elem, field))
        tablePath = '/%s/table_%s_%s' % (moose_elem.path, elem, field)
        tab = moose.Table2(tablePath)
        moose.connect(tab, 'requestOut', moose_elem, 'get' + field[0].upper() + field[1:])
        self.tables["%s/%s.%s" % (self.__prefix__, elem, field)] = tab
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
        if self.G.graph['graph'].get('solver', 'ksolve') == 'ksolve':
            dt = eval(self.G.graph['graph'].get('dt', '0.01'))
            pu.info("Using dt=%s for all chemical process" % dt)
            for i in range(10, 16):
                moose.setClock(i, dt)
        else:
            plotDt = eval(self.G.graph['graph'].get('plot_dt', 1))
            pu.info("Using plot_dt of %s for moose.Table2" % plotDt)
            moose.setClock(18, plotDt)

        moose.reinit()

        if 'sim_time' in self.G.graph['graph']:
            runtime = eval(self.G.graph['graph']['sim_time'])
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

def main():
    pass

if __name__ == '__main__':
    main()
