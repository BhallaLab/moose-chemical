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
        self.n = 0
        self.assign(attribs)

    def assign(self, attribs):
        if 'conc_init' in attribs:
            self.conc = float(attribs['conc_init'])
        elif 'n_init' in attribs:
            self.concOrN = 'n'
            self.n = int(attribs['n_init'])
        else: 
            if 'conc' in attribs:
                self.conc = str(attribs['conc'])
            elif 'n' in attribs:
                self.n = attribs['n']
                self.concOrN = 'n'
            else:
                pu.warn(["Expecting 'conc_init', 'conc', 'n_init', or 'n'"
                    , "Got: %s" % attribs
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
        self.kinetic = attribs.get('expr', attribs.get('kinetic', None))

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
    if len(set(['conc_init','n_init','n','conc']).intersection(attrset)) != 0:
        if 'constant' in attrset:
            return BufPool(node, attribs)
        else:
            return Pool(node, attribs)

    elif len(set(['kf', 'kb', 'expr', 'kinetic']).intersection(attrset)) != 0:
        return Reaction(node, attribs)
    elif len(set(['enzyme', 'km', 'kcat']).intersection(attrset)) != 0:
        return EnzymaticReaction(node, attribs)
    else:
        pu.fatal("Couldn't determine the type of node: %s" % node)

