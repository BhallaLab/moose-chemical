"""main.py: 

    Load a graphviz chemical model into MOOSE.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


from graphviz import gv
import config
import logging

logger_ = logging.getLogger('yacml')
logger_.setLevel(logging.DEBUG)

def main(args):
    config.args_ = args
    modelFile = args['model_file']
    if args['solver'] == 'moose':
        gv.to_moose(modelFile)
        gv.run(args['sim_time'])
    elif args['solver'] == "scipy":
        logger_.error("Solver scipy is still not supported")
    else:
        logger_.error("Invalid solver: %s " % args['solver'])
    return None

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''YACML: Yet Another Chemical Markup Language'''
    argp = argparse.ArgumentParser(description=description)
    argp.add_argument('--sim_time', '-st'
            , metavar='variable'
            , required = True
            , type = float
            , help = 'A generic option'
            )
    argp.add_argument('--model_file', '-f'
            , required = True
            , type = str
            , help = 'Model file'
            )
    argp.add_argument('--solver', '-s'
            , required = True
            , default = 'moose'
            , type = str
            , help = "Which solver to use: moose | scipy"
            )

    argp.add_argument('--plot', '-p'
            , action = 'store_true'
            , help = "Plot the results?"
            )

    argp.add_argument('--outfile', '-o'
            , required = False
            , default = None
            , type = str
            , help = "Name of the plot file"
            )

    argp.add_argument('--log', '-l'
            , required = False
            , default = 'warning'
            , type = str
            , help = 'Debug levels: [debug, info, warning, error, critical]'
            )

    class Args: pass 
    args = Args()
    argp.parse_args(namespace=args)
    main(vars(args))
