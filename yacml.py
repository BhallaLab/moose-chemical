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


import yacml2moose
import config
import yparser.yparser as yp
import yparser.bnf as bnf
import yparser.pre_processor
import moose
import moose.utils as mu
import lxml.etree as etree

logger_ = config.logger_

def yacml_to_networkx( yacml_file, **kwargs ):
    """yacml_to_networkx Convert yacml model to equivalent networkx graph.

    :param yacml_file: path of yacml file.
    """
    nxG = yp.create_graph( yacml_file, **kwargs )
    pre_processor.pre_process( nxG )
    return nxG

def networkx2moose( nxg, **kwargs ):
    model = yacml2moose.DotModel( nxg, **kwargs )
    return model

def loadYACML(yacml_file, **kwargs):
    """loadYACML Load YACML model into MOOSE.

    :param modelFile: Path of model.
    :param **kwargs:
    """
    xml = yp.parse( yacml_file )
    with open( '%s.xml' % yacml_file, 'w' ) as f:
        f.write( etree.tostring( xml, pretty_print = True ) )
    yacml2moose.load( xml )
    quit( )

    networkxG = yacml_to_networkx( yacml_file )
    # Once graph is preprocess, load it in moose.
    model = networkx2moose.load( networkxG, **kwargs)
    return model

def main(args):
    """Main entry function
    """
    config.args_ = args
    modelFile = args['model_file']
    xml = yp.parse( modelFile )
    yacml2moose.load( xml )
    quit()
    if args['solver'] == 'moose':
        model = yacml2moose.DotModel(modelFile)
        model.run(args)
        return model
    elif args['solver'] == "scipy":
        logger_.error("Solver scipy is still not supported")
    else:
        logger_.error("Invalid solver: %s " % args['solver'])
    return None

# if __name__ == '__main__':
#     import argparse
#     # Argument parser.
#     description = '''YACML: Yet Another Chemical Markup Language'''
#     argp = argparse.ArgumentParser(description=description)
#     argp.add_argument('--model_file', '-f'
#             , required = True
#             , type = str
#             , help = 'Model file'
#             )
#     
#     argp.add_argument('--sim_time', '-st'
#             , metavar='variable'
#             , default = 10.0
#             , type = float
#             , help = 'A generic option'
#             )
# 
#     argp.add_argument('--solver', '-s'
#             , default = 'moose'
#             , type = str
#             , help = "Which solver to use: moose | scipy"
#             )
# 
#     argp.add_argument('--outfile', '-o'
#             , default = None
#             , type = str
#             , help = "Name of the plot file"
#             )
# 
#     argp.add_argument('--log', '-l'
#             , default = 'warning'
#             , type = str
#             , help = 'Debug levels: [debug, info, warning, error, critical]'
#             )
# 
#     class Args: pass 
#     args = Args()
#     argp.parse_args(namespace=args)
#     main(vars(args))
