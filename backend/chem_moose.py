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

import logging
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filename='default.log',
    filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
_logger = logging.getLogger('cv2moose.to_moose')
_logger.addHandler(console)

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
        reac.connect('sub', subPath, 'reac')
    for prd in attribs.get('prds', []): 
        prdPath = get_molecule_path(compt, prd)
        reac.connect('prd', prdPath, 'reac')

    if attribs.get('expr', None) is not None:
        add_expression_to_reac(reac, attribs)
    else:
        reac.Kf = float(attribs['kf'])
        reac.Kb = float(attribs['kb'])
        _logger.info("Rate constants: kf=%s, kb=%s" % (reac.Kf, reac.Kb))
    return reac

def add_expression_to_reac(reacElem, attribs):
    """Setup MOOSE reaction with moose.Function having expression
    """
    expr = attribs['expr']


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
        moose.setClock(i, 0.01)
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

