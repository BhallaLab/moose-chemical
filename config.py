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
    filename='__yacml__.log',
    filemode='w')

def add_console_stream(logger):
    """Setup a console logger"""
    global args_
    console = logging.StreamHandler()
    console.setLevel(log_levels_.get(args_['log'], 'warning'))
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)
