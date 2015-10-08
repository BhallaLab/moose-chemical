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
        if 'conc_init' in attribs:
            self.concInit = float(attribs['conc_init'])
        elif 'n_init' in attribs:
            self.concOrN = 'n'
            self.nInit = int(attribs['n_init'])
        else:
            pass
        if 'n_rate' in attribs:
            self.concOrN = 'n'
            self.n = attribs['n_rate']
            self.rate = True
        elif 'conc_rate' in attribs:
            self.concOrN = 'conc'
            self.conc = attribs['conc_rate']
            self.rate = True
        else: 
            if 'conc' in attribs:
                self.conc = str(attribs['conc'])
            elif 'n' in attribs:
                self.n = attribs['n']
                self.concOrN = 'n'
            else:
                pu.warn(["Expecting one of the following"
                , "conc, n, conc_init, n_init, conc_rate, n_rate" 
                , "Got %s" % (",".join(attribs.keys()))
                ])

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
        self.kb = attribs.get('kb', 0)
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


def determine_type(node, graph):
    """Determine the type of node """
    attribs = graph.node[node]
    attrset = set(attribs)
    poolIdentifiers = ['conc_init','n_init','n','conc', 'conc_rate', 'n_rate']
    varIdentifiers = [ node ]
    reacIdentifiers = [ 'kf', 'kb', 'rate_of_reac']
    enzymeIdentifier = [ 'km', 'enzyme', 'kcat']

    if len(set(poolIdentifiers).intersection(attrset)) != 0:
        if 'constant' in attrset:
            return BufPool(node, attribs)
        else:
            return Pool(node, attribs)
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
