"""reac_expr.py: 

    A class representing reaction.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

from config import logger_
import warnings
import moose
import ast

def constant_and_variables(expr, constants):
    # consts 
    expr = expr.replace(" ", "")
    for k in constants:
        if k in expr:
            # This is a constant, replace it with its value.
            expr = expr.replace(k, str(constants[k]))

    index_list = []
    variables = []
    exprAst = ast.parse(expr)
    i = 0
    for node in ast.walk(exprAst):
        if type(node) == ast.Name:
            k = node.id
            if k not in variables:
                replaceWith = 'x%s' % i
                index_list.append((i, k))
                variables.append(k)
                i += 1

    # NOTICE: We must replace the largest variable name first e.g. if Rabs
    # and Rab are two variable then replacing Rab with x0 will also turn
    # Rabs to x0s which is not correct.
    index_list.sort(key=lambda x: len(x[1]))
    for replace, key in reversed(index_list):
        expr = expr.replace(key, 'x%s'%replace)
    return expr, index_list


class Reaction( ):

    def __init__(self, label, edge, graph):
        self.label = label
        self.subs = set()
        self.prds = set()
        self.type = -1
        self.expr = None
        self.kf = -1
        self.kb = -1
        self.attrs = {}
        self.init(edge, graph)
        self.reduced_expr = None

    def __repr__(self):
        msg = "Reac(%s): " % self.label
        subsExpr = ",".join(self.subs)
        prdExpr = ",".join(self.prds)
        if self.expr:
            msg += "%s -- " % subsExpr
            msg += "kinectic=%s" % self.expr
            msg += "--> " + prdExpr
        else:
            msg += subsExpr + " <-- "
            msg += "kb=%s, kf=%s" %  (self.kb, self.kf)
            msg += " --> " + prdExpr
        return msg

    def __str__(self):
        return self.__repr__()

    def init(self, edge, graph):
        src, tgt = edge
        self.subs.add(src)
        self.prds.add(tgt)
        self.attrs.update(graph[src][tgt])
        if "kinetic" in graph[src][tgt]:
            logger_.info("Adding a reaction with expression")
            self.type = 1
            self.expr = graph[src][tgt]['kinetic']
        elif "kf" in graph[src][tgt] and "kb" in graph[src][tgt]:
            logger_.info("Adding a reaction with rate contants")
            self.type = 0
            self.kf = graph[src][tgt]['kf']
            self.kb = graph[src][tgt]['kb']
        else:
            self.type = -1
            warnings.warn("This reaction does not have any kinetic expression"
                    + " Or rate constant Kf (and Kb)"
                    )

    def update(self, edge, graph):
        """A new edge of the same reaction
        Check that params are same on it edge.
        Add sub and prd to list of subs and prds.
        """
        src, tgt = edge
        if self.type == 1:
            assert self.expr == graph[src][tgt]['kinetic']
        elif self.type == 0:
            assert self.kf == graph[src][tgt]['kf']
            assert self.kb == graph[src][tgt]['kb']
        self.subs.add(src)
        self.prds.add(tgt)

    def get_type(self):
        return self.type

    def insert_into_moose(self, reacPath, molecules):
        logger_.info("Inserting into moose: %s" % self)
        if self.type == 0:
            r = moose.Reac(reacPath)
            self.add_reaction(r, molecules)
        elif self.type == 1:
            self.add_kinetics(reacPath, molecules)

    def add_reaction(self, reac, molecules):
        """
        Insert this reaction into moose.
        """
        logger_.info("Adding reaction: " % self)
        for sub in self.subs:
            reac.connect('sub', molecules[sub], 'reac')
        for prd in self.prds:
            reac.connect('prd', molecules[prd], 'reac')
        reac.Kf, reac.Kb = self.kf, self.kb

    def add_kinetics(self, reacPath, molecules):
        '''Add a kinetic to reaction.

        Each reaction can only have one kinetic.
        '''

        kineticPath = '{}_expr'.format(reacPath)
        func, subsList = self.add_function(kineticPath)
        # Apply the variable map.
        for i, pool in subsList:
            try:
                molecule = molecules[pool]
            except IndexError:
                logger_.warn([ "Molecule %s not found" % molecule
                    , "Available molecules: {}".format(" ".join(self.molecules.keys()))
                    ])
            logger_.debug("%s is a input to function" % molecule)
            if isinstance(molecule, moose.Pool):
                try: 
                    logger_.debug("Connecting %s to x[%s]" % (molecule, i))
                    moose.connect(molecule, 'nOut', func.x[i], 'input')
                except IndexError as e:
                    logger_.error("func.num is set to {}, trying to access {}".format(
                        len(func.x), i)
                        )
                    sys.exit()

            elif isinstance(molecule, moose.Function):
                moose.connect(molecule, 'valueOut', func.x[i], 'input')
            else:
                logger_.error("This molecule type %s not supported" % molecule)

        moose.connect(func, 'valueOut', molecules[subs], 'decrement')
        moose.connect(func, 'valueOut', molecules[prd], 'increment')

        return func, False

    def add_function(self, funcPath):
        """Add a function with given expression """

        func = moose.Function(funcPath)
        self.reduced_expr, subsList = constant_and_variables(self.expr, self.attrs)
        logger_.debug("Reduced expr : %s" % self.reduced_expr
                + "Vars (with x_index) are: %s" % subsList
                )
        func.x.num = len(subsList)
        func.mode = 1    # just compute the function value.
        func.expr = str(self.reduced_expr)
        # Add to available kinetics.
        return func, subsList

class ReactionsSet():

    def __init__(self, modelname):
        self.scope = modelname
        self.reactions = {}

    def __len__(self):
        return len(self.reactions)

    def __iter__(self):
        return iter(self.reactions)

    def __getitem__(self, k):
        return self.reactions[k]

    def add_reaction(self, edge, graph):
        """Add a reaction into this network"""
        src, tgt = edge
        reacname = graph[src][tgt]['label']

        # This reaction is already present. Update its parameters.
        if reacname in self.reactions:
            self.reactions[reacname].update(edge, graph)

        # create a new reaction.
        reac = Reaction(reacname, edge, graph)
        self.reactions[reacname] = reac
