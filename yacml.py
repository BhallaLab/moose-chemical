"""yacml.py: 

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"


import chemviz
import config
import moose.utils as mu
from yparser import yparser
from yparser import pre_processor

logger_ = config.logger_

def loadYACML(modelFile, **kwargs):
    """loadYACML Load YACML model into MOOSE.

    :param modelFile: Path of model.
    :param **kwargs:
    """

    networkxG = yparser.create_graph( modelFile )

    # Pre-process the expressions on graph.
    pre_processor.pre_process( networkxG )

    # Once graph is preprocess, load it in moose.
    model = chemviz.DotModel( networkxG )

    return model

def main(args):
    """Main entry function
    """
    config.args_ = args
    modelFile = args['model_file']
    if args['solver'] == 'moose':
        model = chemviz.DotModel(modelFile)
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
    argp = argparse.ArgumentParser(description=description)
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

    class Args: pass 
    args = Args()
    argp.parse_args(namespace=args)
    main(vars(args))
