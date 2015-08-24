"""parser.py: 

    A parser of chemical network.

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2015, Dilawar Singh and NCBS Bangalore"
__credits__          = ["NCBS Bangalore"]
__license__          = "GNU GPL"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import sys
import pyparsing as pp
import pprint

compartment_ = pp.Keyword("compartment")
properties_ = pp.Keyword("properties")
molecule_ = pp.Keyword("molecule")
reaction_ = pp.Keyword("reaction")
left_ = pp.Keyword('<--')
right_ = pp.Keyword('-->')
both_ = pp.Keyword('<->')

lbrace_ = pp.Literal('{').suppress()
rbrace_ = pp.Literal('}').suppress()
semi    = pp.Literal(';').suppress()
equal   = pp.Literal('=').suppress()
dot     = pp.Literal('.').suppress()
colon   = pp.Literal(':').suppress()
end     = pp.ZeroOrMore(semi)

# identifier
identifier = pp.Word( pp.alphas+"_", pp.alphanums+"_").setName("identifier")

# This is from here 
# http://pyparsing.wikispaces.com/UserContributions
floater = pp.Regex(r"-?\d+(\.\d*)?([Ee][+-]?\d+)?")
floater.setParseAction(lambda toks:float(toks[0]))
 
# Expression
lhs = identifier
kinetic_expr = pp.QuotedString(quoteChar='"', multiline=True)
value_expr = floater 
expression = value_expr | kinetic_expr 
rhs = expression 
assignment = pp.Group(lhs + equal  + expression + semi).setResultsName("assignment")

# molecule 
molecule_props  = pp.OneOrMore( assignment ).setResultsName("props")
molecule = molecule_ + identifier + lbrace_ + molecule_props + rbrace_ + end

# eaction.
reac_name = identifier.setResultsName("identifier")
reac_type = left_ | right_ | both_
stoichiometry = pp.Group(pp.delimitedList( identifier, delim='+') + reac_type \
        + pp.delimitedList(identifier, delim='+')).setResultsName("stoich")

reac_params = pp.Group(pp.OneOrMore( assignment )).setResultsName("reac_params")
reac_expr = stoichiometry + lbrace_ + reac_params + rbrace_ + end
reaction = pp.Group(reaction_ + reac_name + colon + reac_expr).setResultsName("reaction")

local_reaction = reaction

compt_props = properties_ + lbrace_ + pp.Dict(pp.OneOrMore(assignment)) + rbrace_ + end
compartment_expr = pp.Group(compt_props | molecule | local_reaction).setResultsName("compt_expr")

compartment = pp.Group(compartment_ + identifier + lbrace_ \
        + pp.OneOrMore(compartment_expr) + rbrace_ \
        + end).setResultsName("compartment")

model = (pp.OneOrMore(compartment | reaction)).setResultsName("network")
# comment and whitespace
single_line_comment = '//' + pp.restOfLine
model.ignore(single_line_comment)
model.ignore(pp.cStyleComment)

def parse(filename):
    tokens = None
    try:
        tokens = model.parseFile(filename)
    except Exception as err:
        print err.line
        print " "*(err.column-1) + "^"
        print err
    return tokens

def main(filename):
    print("testing %s" % filename)
    parse(filename)

if __name__ == '__main__':
    filename = sys.argv[1]
    main(filename)
