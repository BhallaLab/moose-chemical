"""moose.py: 

    MOOSE backend.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import moose
import moose.utils as mu
import warnings
import utils
import re
import config 
import logging

_logger = logging.getLogger('yacml.moose')

table_path_ = '/tables'
moose.Neutral(table_path_)

def add_recorder(moose_pool):
    """Add a table for given pool """
    table = moose.Table2('%s/%s' % (table_path_, moose_pool.name))
    _logger.info("Adding a table2 for species %s" % moose_pool.name)
    table.connect('requestOut', moose_pool, 'getConc')
    return table

def add_species(compt, species, attribs):
    """Add a species under compartment """
    _logger.info("Adding species %s under %s" % (species, compt.path))
    _logger.debug("++ With attributes: %s" % attribs)

    poolPath = "%s/%s" % (compt.path, species)
    buffered = attribs.get('buffered', False)  

    p = None
    if not buffered: p = moose.Pool(poolPath)
    else: p = moose.BufPool(poolPath)

    if attribs.get('conc_init', None) is not None:
        p.concInit = float(attribs['conc_init'])
    elif attribs.get('n_init', None) is not None:
        p.nInit = float(attribs['n_init'])
    else:
        msg = [ "Species %s should have conc_init or n_init" % species
                , "Using default value"
                ]
        utils.warn(msg)

    if attribs.get('record', True):
        add_recorder(p)
    return p


def add_compartment(compt_dict):
    """Add a compartment """
    compts = compt_dict.keys()
    compt = None
    for comptName in compts:
        comptPath = '/%s' % comptName
        attribs = compt_dict[comptName]
        comptType = attribs.get('geometry', 'cube')
        _logger.info("Adding compartment %s (%s)" % (comptName, comptType))

        if comptType == 'cube':
            compt = moose.CubeMesh(comptPath)
        elif comptType == 'cylinder':
            compt = moose.CylMesh(comptPath)
        else:
            utils.warn("Type %s is not supported" % comptType)
    compt.volume = float(attribs['volume'])

    speciesies = attribs.get('species', [])
    [ add_species(compt, s, speciesies[s]) for  s in speciesies ]

    subReacs = attribs.get('reaction', [])
    [ add_reaction_intercompartment(compt, reac, subReacs[reac]) for 
            reac in subReacs ]

    return compt

def get_molecule_path(compt, molecule):
    """Get the MOOSE element for molecule in compt"""
    path = "%s/%s" % (compt.path, molecule)
    if moose.exists(path):
        return moose.Neutral(path)
    else:
        msg = "There is not Pool/BufPool in compartment %s. " % compt.name
        msg += " Please check your species list."
        utils.fatal(msg)

def add_reaction_intercompartment(compt, reac_name, attribs):
    """Add a reaction to moose"""
    reacPath = "%s/%s" % (compt.path, reac_name)
    _logger.info("Adding reaction under %s" % reacPath)
    reac = moose.Reac(reacPath)
    for sub in attribs.get('subs', []): 
        subPath = moose.Neutral('%s/%s' % (compt.path, sub))
        _logger.debug("++ Adding substrate: %s" % subPath)
        reac.connect('sub', subPath, 'reac')
    for prd in attribs.get('prds', []): 
        prdPath = get_molecule_path(compt, prd)
        _logger.debug("++ Adding product: %s" % prdPath)
        reac.connect('prd', prdPath, 'reac')

    if attribs.get('expr', None) is not None:
        add_expression_to_reac(reac, attribs)
    else:
        reac.Kf = float(attribs['kf'])
        reac.Kb = float(attribs['kb'])
        _logger.debug("Rate constants: kf=%s, kb=%s" % (reac.Kf, reac.Kb))
    return reac

def format_expression(expr, moose_reac, attribs):
    """
    Add an expression to moose_reac. Return a mapping of x's and variables to
    map to.
    """
    # replace the init concentration by their value, if any. 
    subs, prds = [], []
    for pp in moose_reac.neighbors['sub']:
        for p in pp: subs.append(p)
    for pp in moose_reac.neighbors['prd']:
        for p in pp: prds.append(p)
    for p in subs + prds:
        key = '%s#0' % p.name 
        value = p.concInit
        expr = expr.replace(key, "%s" % value)

    if "_init" in expr:
        utils.fatal([ "Malformed expression: %s." % expr
            , "One or more _init don't exists in compartment"]
            )

    # replace the constant with their values.
    sorted_attribs = sorted(attribs, key=lambda x: 1.0/len(x))
    for attrib in sorted_attribs:
        key, val = attrib, attribs[attrib]
        try:
            val = float(val)
            expr = expr.replace(key, "%s" % val)
        except:
            # This is not a constant.
            pass
    # By now all we should have in our expressions are either decimal numbers or
    # variables. 
    # finally we rewrite x as x0.
    expr = expr.replace('x', 'x0')
    return expr
    
def add_expression_to_reac(reacElem, attribs):
    """Setup MOOSE reaction with moose.Function having expression
    """
    expr = attribs['expr']
    expr = format_expression(expr, reacElem, attribs)
    # Create a function.
    funcPath = '%s/func' % reacElem.path
    func = moose.Function(funcPath)
    func.mode = 1
    _logger.info("Adding expression %s" % expr)
    func.expr = expr

    # Take any product (they all increase with same rate) and setup the message.
    # The output of function must decrement the values of substrate and increase
    # the value of product.
    for ss in reacElem.neighbors['sub']:
        for s in ss:
            func.connect('valueOut', s, 'decrement')
    for pp in reacElem.neighbors['prd']:
        for p in pp:
            func.connect('valueOut', s, 'increment')


def add_global_reaction(reac):
    """Add intercompartment reactions"""
    pass

def to_moose(ymlmodel, **kwargs):
    """Convert given tokens into MOOSE model"""
    compartments = ymlmodel.get('compartment', [])
    reactions = ymlmodel.get('reaction', [])
    [ add_compartment(compt) for compt in compartments ]
    [ add_global_reaction(reac) for reac in reactions ]

def run(args, **kwargs):
    for i in range(10, 16):
        moose.setClock(i, 0.001)
    moose.reinit()
    moose.start(args['sim_time'])
    tables = moose.wildcardFind('/tables/##[TYPE=Table2]')
    records_ = {}
    [ records_.__setitem__(t.name,t) for t in tables ]
    if args.get('plot', None):
        if args.get('outfile', None) is not None:
            mu.plotRecords(records_
                    , subplot=True
                    , outfile=args['outfile']
                    )
        else:
            mu.plotRecords(records_
                    , subplot=True
                    )
            plt.show()
    return records_

