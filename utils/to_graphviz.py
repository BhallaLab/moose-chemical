"""to_graphviz.py: 

Convert model to graphviz

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

names_ = { }
graphviz_ = []

def add_to_gv( line, indent = 1 ):
    global graphviz_
    for i in range( indent ):
        line = '  ' + line
    if line not in graphviz_:
        graphviz_.append( line )

def graphviz_text( ):
    global graphviz_ 
    return "\n".join( graphviz_ )

##
# @brief Generate a unique name from given moose element.
#
# @param path
#
# @return name
def yacml_name( elem ):
    global names_
    path = elem.path
    p = path.replace( '[0]', '' )
    name = "_".join( p.split('/')[-2:] )
    name = name.replace( '<-', '__' )
    name = name.replace( '->', '__' )
    names_[name] = elem.path
    return '"%s"' % name

def init_graphviz( modelname ):
    add_to_gv( 'digraph %s { ' % modelname, 0 )
    add_to_gv( 'graph[ overlap=scale ];' )

def end_graphviz( ):
    add_to_gv( "}", 0 );
    

def write_graphviz( modelname ):
    init_graphviz( modelname )
    reacs = moose.wildcardFind( '/yacml/##[TYPE=Reac]' )
    zreacs = moose.wildcardFind( '/yacml/##[TYPE=ZombieReac]' )
    for r in reacs + zreacs:
        add_to_gv( '%s[label="", shape=rect];' % ( yacml_name(r) ) )

    for r in reacs + zreacs:
        subs = r.neighbors['sub']
        prds = r.neighbors['prd']
        for s in subs:
            add_to_gv( '%s -> %s;' % (yacml_name(r), yacml_name(s) ) )
        for p in prds:
            add_to_gv( '%s -> %s;' % ( yacml_name(p), yacml_name(r) ) )

    end_graphviz( )
    dotFile = '%s.dot' % modelname
    with open( dotFile, 'w' ) as f:
        f.write( graphviz_text() )
    print( '[INFO] Wrote network topology to %s' % dotFile )
