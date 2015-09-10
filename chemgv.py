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
    if args.get('all', False):
        from test import test_gv
        test_gv.main()
        quit()

    modelFile = args['model_file']
    if args['solver'] == 'moose':
        model = gv.DotModel(modelFile)
        model.run(args)
        return model
    elif args['solver'] == "scipy":
        logger_.error("Solver scipy is still not supported")
    else:
        logger_.error("Invalid solver: %s " % args['solver'])
    return None

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''YACML: Yet Another Chemical Markup Language'''
    parser = argparse.ArgumentParser(description=description)
    subparser = parser.add_subparsers()

    argp = subparser.add_parser('run', help = 'run model')
    argp.add_argument('--model_file', '-f'
            , required = True
            , type = str
            , help = 'Model file'
            )
    
    argp.add_argument('--sim_time', '-st'
            , metavar='variable'
            , default = 10.0
            , type = float
            , help = 'A generic option'
            )

    argp.add_argument('--solver', '-s'
            , default = 'moose'
            , type = str
            , help = "Which solver to use: moose | scipy"
            )

    argp.add_argument('--plot', '-p'
            , action = 'store_true'
            , help = "Plot the results?"
            )

    argp.add_argument('--outfile', '-o'
            , default = None
            , type = str
            , help = "Name of the plot file"
            )

    argp.add_argument('--log', '-l'
            , default = 'warning'
            , type = str
            , help = 'Debug levels: [debug, info, warning, error, critical]'
            )

    argt = subparser.add_parser('test', help = 'Test module')
    argt.add_argument('--all', '-a'
            , required = True
            , action = 'store_true'
            , help = 'Test this module'
            )

    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main(vars(args))
