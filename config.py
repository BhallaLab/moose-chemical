"""config.py: 

    This is the configuration file for this library.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import logging

args_ = {}

log_levels_ = { 
        'debug' : logging.DEBUG
        , 'info' : logging.INFO
        , 'warning' : logging.WARNING
        , 'error' : logging.ERROR
        , 'critical' : logging.CRITICAL
        }


logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
    filemode='w'
    )

pool_shape_ = 'ellipse'
bufpool_shape_ = 'egg'
reaction_shape_ = 'rect'
enzyme_reac_shape_ =  'egg'
