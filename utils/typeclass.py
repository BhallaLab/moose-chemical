"""typeclass.py: 

    Implement a bare-bone static typing on graph.

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
import moose.print_utils as pu
from .  import expression as exp_

class Pool(object):
    """Pool"""
    def __init__(self, name,  attribs):
        super(Pool, self).__init__()
        self.name = name
        self.concOrN = 'conc'
        self.conc = 0.0
        self.concInit = 0.0
        self.nInit = 0.0
        self.n = 0
        self.rate = False
        self.assign(attribs)

    def assign(self, attribs):

        # Do the initialization.
        if 'conc_init' in attribs:
            self.concInit = float(attribs['conc_init'])
        elif 'N_init' in attribs:
            self.concOrN = 'n'
            self.nInit = float(attribs['N_init'])
        else:
            pass

        # Get the rate. If rates are not specified then get the conc or n
        # expression.
        if 'N_rate' in attribs:
            self.concOrN = 'n'
            self.n = attribs['N_rate']
            self.rate = True
            return None
        elif 'conc_rate' in attribs:
            self.concOrN = 'conc'
            self.conc = attribs['conc_rate']
            self.rate = True
            return None
        else:
            pass

        exprObj = attribs['expr_obj']
        if 'conc' in attribs:
            self.concOrN = 'conc'
            self.conc = exprObj.expr_val
            #self.conc = attribs.get('reduced_expr', attribs['conc'])
        elif 'N' in attribs:
            self.n = attribs.get('reduced_expr', attribs['N'])
            self.concOrN = 'n'

class BufPool(Pool):
    """docstring for BufPool"""

    def __init__(self, name, attribs):
        Pool.__init__(self, name, attribs)


class Enzyme(object):
    """docstring for Enzyme"""

    def __init__(self, name, attribs):
        try:
            self.km = float(attribs['km'])
        except:
            self.km = attribs['km']

        try:
            self.kcat = float(attribs['kcat'])
        except:
            self.kcat = attribs['kcat']

class Reaction(object):
    """docstring for Reaction"""
    def __init__(self, name, attribs):
        super(Reaction, self).__init__()
        self.name = name
        self.kf = attribs.get('kf', 0)
        self.numKf = attribs.get('numKf', 0)
        self.kb = attribs.get('kb', 0)
        self.numKb = attribs.get('numKb', 0)
        self.rate = attribs.get('rate_of_reac')

class Variable(object):
    """Docstring for Variable"""
    def __init__(self, name, attribs):
        super(Variable, self).__init__()
        self.name = name
        self.assign(attribs)
        self.expr = None
        # Mode 0 for simple expression, 1 for differential equation.
        self.mode = "val"

    def assign(self, attibs):
        if self.name in attibs:
            self.expr = str(attibs[self.name])
        elif "%s_rate" % self.name in attibs:
            self.expr = str(attibs["%s_rate" % self.name])
            self.mode = "rate"
        else:
            raise UserWarning("Could not find {0} or {0}_rate".format(self.name))

class EnzymaticReaction(Reaction):
    """docstring for EnzymaticReaction"""

    def __init__(self, name, attribs):
        Reaction.__init__(self, name, attribs)
        self.name = name
        self.enzyme = attribs['enzyme']
        self.attribs = attribs

class ReducedExpr():
    def __init__(self, expr):
        expr = expr.replace('"', '')
        self.expr = expr
        self.parsed_expr = None
        self.expr_val = expr
        self.val_type = "string"
        self.init()

    def __str__(self):
        return "%s" % self.expr_val

    def init(self):
        try:
            self.parsed_expr = exp_.parser.parse(self.expr)
        except:
            self.parsed_expr = None 
        if self.parsed_expr:
            try:
                self.expr_val = self.parsed_expr.evaluate({})
                self.val_type = "decimal"
            except Exception as e:
                self.expr_val = self.parsed_expr.toString()
                self.val_type = "string"

def determine_type(node, graph):
    """Determine the type of node """
    attribs = graph.node[node]
    attrset = set(attribs)
    poolIdentifiers = ['conc_init','N_init','N','conc', 'conc_rate', 'N_rate']
    varIdentifiers = [ node ]
    reacIdentifiers = [ 'kf', 'kb', 'numKf', 'numKb', 'rate_of_reac']
    enzymeIdentifier = [ 'km', 'enzyme', 'kcat']

    expr = attribs.get('conc', attribs.get('N', ''))

    exprObj = None
    if expr:
        reducedExpr = exp_.replace_possible_subexpr(expr, attribs, exp_.get_ids(expr))
        exprObj = ReducedExpr(reducedExpr)
        attribs['expr_obj'] = exprObj
    else:
        attribs['expr_obj'] = None

    if len(set(poolIdentifiers).intersection(attrset)) != 0:
        if len(set(['constant']).intersection(attrset)) != 0:
            attribs['reduced_expr'] = exprObj.expr_val
            return BufPool(node, attribs)
        elif exprObj is not None:
            attribs['reduced_expr'] = exprObj.expr_val
            if exprObj.val_type == "decimal":
                return Pool(node, attribs)
            elif exprObj.val_type == "string":
                return BufPool(node, attribs)
            else:
                raise Exception("Invalid value type %s" % exprObj.val_type)
        else:
            attribs['reduced_expr'] = exprObj.expr_val
            return BufPool(node, attribs)

    if len(set(varIdentifiers).intersection(attrset)) != 0:
        return Variable(node, attribs)
    elif len(set(reacIdentifiers).intersection(attrset)) != 0:
        return Reaction(node, attribs)
    elif len(set(enzymeIdentifier).intersection(attrset)) != 0:
        return EnzymaticReaction(node, attribs)
    else:
        pu.warn("Couldn't determine the type of node: %s" % node)
        pu.info( [ "Following sets are used to indenfy types of nodes" 
            , "Pools : %s" % (",".join(poolIdentifiers))
            , "Variables: %s" % (",".join(varIdentifiers))
            , "Reaction: %s" % (",".join(reacIdentifiers)) ]
            )
