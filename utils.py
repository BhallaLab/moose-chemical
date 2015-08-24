"""utils.py: 

Some utility functions.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def format_msg(msg):
    if type(msg) == list:
        msg = "\n++ ".join(msg)
        return msg
    return msg

def warn(msg):
    msg = format_msg(msg)
    print( "[WARN] " +  bcolors.WARNING + msg + bcolors.ENDC )

def fatal(msg):
    msg = format_msg(msg)
    print("[FATAL]" + bcolors.FAIL + msg + bcolors.ENDC )
    quit()
