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
import libsbml as sbml
import warnings
import moose
import ast


class DotModel():
    '''http://www.ncbi.nlm.nih.gov/pmc/articles/PMC1414565/
    '''

    def __init__(self, modelFile):
        self.filename = modelFile
        self.G = nx.DiGraph()
        self.molecules = {}
        self.reactions = {}
        self.poolPath = '/pool'
        self.reacPath = '/reac'
        self.modelPath = '/model'
        self.funcPath = '/function'
        self.variables = {}


    def initSBML(self):
        self.sbmlDoc = sbml.SBMLDocument(3, 1)
        self.model = self.sbmlDoc.createModel()
        self.model.setTimeUnits("second")
        self.model.setExtentUnits("mole")
        self.model.setSubstanceUnits('mole')

    def initMOOSE(self):
        """Initialize paths in MOOSE"""
        for path in [self.poolPath, self.funcPath, self.reacPath, self.modelPath]:
            moose.Neutral(path)

    def addMolecules(self, compartment_id = None, **kwargs):
        ''' Each node in graph is a molecule, add them to graphviz network.
        '''
        for n in self.G:
            nInit = float(self.G.node[n].get('n_init', 0))
            # SI mole/m^3 to mole/litre
            concInit = 1e3 * float(self.G.node[n].get('conc_init', 0))

            if n in self.molecules:
                continue
            if not compartment_id:
                compartment_id = 'comp_%s' % n
                compartmentVolume = float(self.G.node[n]['volume'])
                compartment = self.model.createCompartment()
                compartment.setId(compartment_id)
                compartment.setConstant(kwargs.get('compartment_const', True))
                compartment.setSpatialDimensions(3)
                compartment.setUnits('litre')

            s1 = self.model.createSpecies()
            s1.setId(n)
            s1.initDefaults()
            if nInit: s1.setInitialAmount(nInit)
            elif concInit: s1.setInitialConcentration(concInit)

            s1.setConstant(False)
            s1.setBoundaryCondition(False)
            s1.setCompartment(compartment_id)
            # Add to list for future reference.
            self.molecules[n] = s1

    def createNetwork(self):
        """Create chemical network """
        self.G = nx.read_dot(self.filename)
        # We don't want MultiDiGraph.
        self.G = nx.DiGraph(self.G)
        assert self.G.number_of_nodes() > 0, "Zero molecules"

    def toSBML(self, outfile):
        self.initSBML()
        self.createNetwork()
        self.addMolecules()
        self.addReactions()
        if not outfile:
            print sbml.writeSBMLToString(self.sbmlDoc)
        else:
            sbml.writeSBMLToFile(self.sbmlDoc, outfile)

    def addReactions(self):
        for s, t in self.G.edges():
            edgeDict = self.G[s][t]
            reacId = str(edgeDict['id'])
            kinetic = str(edgeDict['kinetic'])
            expr = None
            if kinetic:
                expr = sbml.parseL3Formula(kinetic)
            if expr: 
                self.addReaction(s, t, reacId, expr)

    def addReaction(self, substrate, product, reacId, expr, **kwargs):
        '''Each edge is a reaction '''

        print("[REAC] Adding reaction %s" % reacId)
        if reacId in self.reactions:
            print("Warning: Reaction %s is already loaded" % reacId)
            return

        r1 = self.model.createReaction()
        r1.initDefaults()
        r1.setId(reacId)
        r1.setReversible(True)
        r1.setFast(False)

        subs = r1.createReactant()
        subs.setConstant(False)
        subs.setSpecies(substrate)
        prod = r1.createProduct()
        prod.setSpecies(product)
        prod.setConstant(False)

        k1 = r1.createKineticLaw()
        k1.setMath(expr)
        self.reactions[reacId] = r1

if __name__ == '__main__':

    def writeSBMLModel(dot_file, outfile = None):
        model = DotModel(dot_file)
        model.createNetwork()
        model.writeSBML(outfile)

    def main():
        writeSBMLModel(dot_file = "./smolen_baxter_bryne.dot"
                , outfile = "smolen_baxter_bryne.sbml"
                )

    main()
